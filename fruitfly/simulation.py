"""Vectorized whole-connectome, current-based leaky integrate-and-fire model."""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path

import numpy as np


class ConnectomeSimulation:
    """All neurons and every dataset edge participate in every integration step.

    This is a deliberately simplified LIF model, not a biological reproduction.
    Edge synapse counts become signed currents after global normalization.
    """
    def __init__(self, cache: Path, seed: int = 7):
        self.manifest = json.loads((cache / "manifest.json").read_text())
        self.pre = np.load(cache / "pre.npy", mmap_mode="r")
        self.post = np.load(cache / "post.npy", mmap_mode="r")
        self.weight = np.load(cache / "weights.npy", mmap_mode="r")
        self.side = np.load(cache / "side.npy", mmap_mode="r")
        self.motion = np.load(cache / "visual_motion.npy", mmap_mode="r")
        self.objects = np.load(cache / "visual_object.npy", mmap_mode="r")
        self.auditory = np.load(cache / "auditory.npy", mmap_mode="r")
        self.motor = np.load(cache / "motor.npy", mmap_mode="r")
        self.xyz = np.load(cache / "xyz.npy", mmap_mode="r")
        n = self.manifest["neurons"]
        self.v = np.zeros(n, np.float32)
        self.spikes = np.zeros(n, np.float32)
        self.rate = np.zeros(n, np.float32)
        self.rng = np.random.default_rng(seed)
        self.stimulus = {"manual_left": 0.0, "manual_right": 0.0, "manual_loom": 0.0,
                         "camera_left": 0.0, "camera_right": 0.0, "audio": 0.0}
        self.source_sequence = {"manual": -1, "camera": -1, "audio": -1}
        self.device_updated = {"camera": 0.0, "audio": 0.0}
        self.paused = False
        self.tick = 0
        self.hz = 0.0
        self.last_step_ms = 0.0
        self.dt_ms = 5.0
        self.lock = threading.Lock()

    def step(self):
        t0 = time.perf_counter()
        # Sparse event propagation: all anatomical edges are represented; only
        # edges from currently spiking presynaptic neurons contribute this tick.
        currents = np.bincount(self.post, weights=self.weight * self.spikes[self.pre],
                               minlength=len(self.v)).astype(np.float32)
        np.tanh(currents / 80.0, out=currents)
        drive = self.rng.normal(.025, .035, len(self.v)).astype(np.float32)
        with self.lock:
            now = time.monotonic()
            if now - self.device_updated["camera"] > .75:
                self.stimulus["camera_left"] = self.stimulus["camera_right"] = 0.0
            if now - self.device_updated["audio"] > .75:
                self.stimulus["audio"] = 0.0
            ml = min(1.0, self.stimulus["manual_left"] + self.stimulus["camera_left"])
            mr = min(1.0, self.stimulus["manual_right"] + self.stimulus["camera_right"])
            loom = self.stimulus["manual_loom"]
            audio = self.stimulus["audio"]
        drive[self.motion & (self.side < 0)] += ml * .28
        drive[self.motion & (self.side > 0)] += mr * .28
        drive[self.objects] += loom * .32
        drive[self.auditory] += audio * .30
        self.v = self.v * .92 + currents * .20 + drive
        fired = self.v >= 1.0
        self.v[fired] = 0.0
        self.spikes[:] = fired
        # Exponentially-smoothed firing rate, converted to spikes/second.
        self.rate = self.rate * .92 + fired * (.08 * (1000.0 / self.dt_ms))
        self.tick += 1
        self.last_step_ms = (time.perf_counter() - t0) * 1000
        self.hz = 1000.0 / max(self.last_step_ms, .001)

    def state(self):
        with self.lock:
            stimulus = dict(self.stimulus)
        total_left = min(1.0, stimulus["manual_left"] + stimulus["camera_left"])
        total_right = min(1.0, stimulus["manual_right"] + stimulus["camera_right"])
        left = self.rate[self.motor & (self.side < 0)]
        right = self.rate[self.motor & (self.side > 0)]
        lm = float(left.mean()) if len(left) else 0.0
        rm = float(right.mean()) if len(right) else 0.0
        # Explicit heuristic motor decoder: bilateral efferent rate drives speed;
        # the left/right difference drives turn. It is not a validated circuit map.
        speed = 0.0 if lm + rm < .001 else min(1.0, (lm + rm) * 12.0)
        turn = 0.0 if abs(rm - lm) < .001 else max(-1.0, min(1.0, (rm - lm) * 10.0))
        # Stable anatomical sample for display; positions are real coordinates,
        # while color is the computed per-neuron activity. This is not parcellation.
        shown = np.linspace(0, len(self.rate) - 1, 900, dtype=np.int64)
        points = np.column_stack((self.xyz[shown, 0], self.xyz[shown, 1], self.rate[shown]))
        return {"tick": self.tick, "step_ms": round(self.last_step_ms, 1), "sim_hz": round(self.hz, 2),
                "active": int(self.spikes.sum()), "mean_rate": float(self.rate.mean()),
                "motor": {"left": lm, "right": rm, "speed": speed, "turn": turn},
                "points": points.round(4).tolist(), "paused": self.paused,
                "stimulus": {**stimulus, "total_left": total_left, "total_right": total_right},
                "dt_ms": self.dt_ms, "simulated_ms": self.tick * self.dt_ms,
                "realtime_factor": round(self.dt_ms / max(self.last_step_ms, .001), 3),
                "model": "whole-network simplified LIF"}

    def run(self):
        while True:
            if not self.paused:
                self.step()
            else:
                time.sleep(.05)
