from __future__ import annotations

import argparse
import json
import threading
import time
import webbrowser
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from .build_cache import build
from .simulation import ConnectomeSimulation


def main():
    parser = argparse.ArgumentParser(description="Fruitfly Connectome Lab")
    parser.add_argument("--data", type=Path, default=Path("fruit_fly_brain_dataset"))
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--rebuild", action="store_true")
    args = parser.parse_args()
    cache = build(args.data, args.rebuild)
    sim = ConnectomeSimulation(cache)
    threading.Thread(target=sim.run, daemon=True).start()
    static = Path(__file__).with_name("static")

    class Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw): super().__init__(*a, directory=str(static), **kw)
        def log_message(self, *_): pass
        def _json(self, obj, status=200):
            body = json.dumps(obj).encode()
            self.send_response(status); self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store"); self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        def do_GET(self):
            if self.path == "/api/state": return self._json(sim.state())
            if self.path == "/api/info": return self._json(sim.manifest)
            return super().do_GET()
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            try: data = json.loads(self.rfile.read(length) or b"{}")
            except ValueError: return self._json({"error": "invalid JSON"}, 400)
            if self.path == "/api/stimulus":
                with sim.lock:
                    source = data.get("source", "manual")
                    client = str(data.get("client_id", "legacy"))[:100]
                    sequence_key = f"{client}:{source}"
                    seq = int(data.get("sequence", sim.source_sequence.get(sequence_key, -1) + 1))
                    if source not in {"manual", "camera", "audio"} or seq <= sim.source_sequence.get(sequence_key, -1):
                        return self._json({"ok": False, "stale": True, "stimulus": sim.stimulus})
                    sim.source_sequence[sequence_key] = seq
                    allowed = {"manual": {"manual_left", "manual_right", "manual_loom"},
                               "camera": {"camera_left", "camera_right"}, "audio": {"audio"}}
                    for k in allowed[source]:
                        if k in data: sim.stimulus[k] = max(0.0, min(1.0, float(data[k])))
                    if source in sim.device_updated: sim.device_updated[source] = time.monotonic()
                return self._json({"ok": True, "stimulus": sim.stimulus})
            if self.path == "/api/pause":
                sim.paused = bool(data.get("paused", not sim.paused)); return self._json({"paused": sim.paused})
            return self._json({"error": "not found"}, 404)

    url = f"http://127.0.0.1:{args.port}"
    print(f"Fruitfly Connectome Lab: {url}")
    print(json.dumps({k: sim.manifest[k] for k in ("neurons", "edges", "unmapped_edges",
                                                    "motion_inputs", "object_inputs", "auditory_inputs", "motor_outputs")}, indent=2))
    if not args.no_browser: threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
