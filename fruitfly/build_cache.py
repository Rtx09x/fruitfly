"""Stream the FlyWire-derived CSV files into compact NumPy arrays."""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import os
import time
from pathlib import Path

import numpy as np

NT_SIGN = {"ACH": 1.0, "OCT": 1.0, "DA": 1.0, "SER": 1.0,
           "GABA": -1.0, "GLUT": -1.0}
CACHE_VERSION = 2


def _rows(path: Path):
    with gzip.open(path, "rt", newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def build(data_dir: Path, force: bool = False) -> Path:
    data_dir = data_dir.resolve()
    cache = data_dir / "cache"
    manifest_path = cache / "manifest.json"
    required = ["neurons.csv.gz", "connections_princeton.csv.gz",
                "classification.csv.gz", "visual_neuron_types.csv.gz"]
    missing = [name for name in required if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Dataset directory is missing: {', '.join(missing)}")
    fingerprint = {}
    for name in required + ["coordinates.csv.gz"]:
        path = data_dir / name
        digest = hashlib.sha256()
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""): digest.update(chunk)
        fingerprint[name] = {"bytes": path.stat().st_size, "sha256": digest.hexdigest()}
    if manifest_path.exists() and not force:
        old = json.loads(manifest_path.read_text(encoding="utf-8"))
        if old.get("source_fingerprint") == fingerprint and old.get("cache_version") == CACHE_VERSION:
            return cache
    cache.mkdir(exist_ok=True)
    started = time.perf_counter()

    neuron_rows = list(_rows(data_dir / "neurons.csv.gz"))
    ids = np.fromiter((int(r["root_id"]) for r in neuron_rows), dtype=np.uint64)
    order = np.argsort(ids)
    ids = ids[order]
    nt_by_id = {int(r["root_id"]): r["nt_type"] for r in neuron_rows}
    id_to_idx = {int(root): i for i, root in enumerate(ids)}
    np.save(cache / "root_ids.npy", ids)

    xyz = np.full((len(ids), 3), np.nan, dtype=np.float32)
    for row in _rows(data_dir / "coordinates.csv.gz"):
        i = id_to_idx.get(int(row["root_id"]))
        if i is not None and np.isnan(xyz[i, 0]):
            xyz[i] = np.fromstring(row["position"].strip("[]"), sep=" ", dtype=np.float32)
    for axis in range(3):
        good = np.isfinite(xyz[:, axis])
        lo, hi = np.percentile(xyz[good, axis], [1, 99])
        xyz[good, axis] = np.clip((xyz[good, axis] - lo) / (hi - lo), 0, 1)
        xyz[~good, axis] = .5
    np.save(cache / "xyz.npy", xyz)

    classification = {int(r["root_id"]): r for r in _rows(data_dir / "classification.csv.gz")}
    visual = {int(r["root_id"]): r for r in _rows(data_dir / "visual_neuron_types.csv.gz")}
    side = np.zeros(len(ids), dtype=np.int8)  # -1 left, +1 right
    visual_motion = np.zeros(len(ids), dtype=np.bool_)
    visual_object = np.zeros(len(ids), dtype=np.bool_)
    auditory = np.zeros(len(ids), dtype=np.bool_)
    motor = np.zeros(len(ids), dtype=np.bool_)
    labels = []
    for i, root in enumerate(ids):
        rid = int(root)
        cls, vis = classification.get(rid, {}), visual.get(rid, {})
        s = cls.get("side") or vis.get("side", "")
        side[i] = -1 if s == "left" else (1 if s == "right" else 0)
        visual_motion[i] = vis.get("subsystem", "").lower() == "motion"
        visual_object[i] = vis.get("subsystem", "").lower() == "object"
        auditory[i] = cls.get("flow") == "afferent" and cls.get("class") == "mechanosensory" and cls.get("sub_class") == "auditory"
        motor[i] = cls.get("flow") == "efferent"
        if len(labels) < 500 and (visual_motion[i] or motor[i]):
            labels.append({"index": i, "root_id": rid, "class": cls.get("class", ""),
                           "type": vis.get("type", ""), "side": s})
    np.save(cache / "side.npy", side)
    np.save(cache / "visual_motion.npy", visual_motion)
    np.save(cache / "visual_object.npy", visual_object)
    np.save(cache / "auditory.npy", auditory)
    np.save(cache / "motor.npy", motor)

    # Count first so files are allocated once. Every CSV edge is retained.
    edge_count = sum(1 for _ in _rows(data_dir / "connections_princeton.csv.gz"))
    pre = np.lib.format.open_memmap(cache / "pre.npy", mode="w+", dtype=np.uint32, shape=(edge_count,))
    post = np.lib.format.open_memmap(cache / "post.npy", mode="w+", dtype=np.uint32, shape=(edge_count,))
    weights = np.lib.format.open_memmap(cache / "weights.npy", mode="w+", dtype=np.float32, shape=(edge_count,))
    unknown = 0
    for j, row in enumerate(_rows(data_dir / "connections_princeton.csv.gz")):
        a, b = id_to_idx.get(int(row["pre_root_id"])), id_to_idx.get(int(row["post_root_id"]))
        if a is None or b is None:
            unknown += 1
            a = 0 if a is None else a
            b = 0 if b is None else b
            syn = 0.0
        else:
            syn = float(row["syn_count"])
        pre[j], post[j] = a, b
        # Sign comes from edge transmitter label; FlyWire transmitter signs are
        # simplified here and are explicitly documented as an assumption.
        weights[j] = syn * NT_SIGN.get(row["nt_type"] or nt_by_id.get(int(row["pre_root_id"]), ""), 1.0)
    pre.flush(); post.flush(); weights.flush()
    manifest = {"cache_version": CACHE_VERSION, "neurons": len(ids), "edges": edge_count, "unmapped_edges": unknown,
                "motion_inputs": int(visual_motion.sum()), "object_inputs": int(visual_object.sum()),
                "auditory_inputs": int(auditory.sum()),
                "motor_outputs": int(motor.sum()), "build_seconds": time.perf_counter() - started,
                "source_files": required, "source_fingerprint": fingerprint, "labels": labels,
                "coordinate_note": "first listed coordinate per root; 1st–99th percentile normalized"}
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return cache
