"""Reproducible baseline/stimulus/input-silencing sanity check."""
from pathlib import Path
from time import perf_counter
from fruitfly.build_cache import build
from fruitfly.simulation import ConnectomeSimulation
import numpy as np

CACHE = build(Path("fruit_fly_brain_dataset"))

def trial(stimulated=True, silenced=False, disconnected=False, steps=100):
    sim = ConnectomeSimulation(CACHE, seed=1)
    if silenced:
        sim.motion_left = sim.motion_left & False
        sim.motion_right = sim.motion_right & False
    if disconnected:
        sim.weight = np.zeros_like(sim.weight)
        sim.connectivity.data[:] = 0
    left, right = [], []
    started = perf_counter()
    for tick in range(steps):
        if stimulated and tick >= 20:
            sim.stimulus.update(manual_left=1.0, manual_right=.1)
        sim.step()
        state = sim.state()["motor"]
        left.append(state["left"]); right.append(state["right"])
    return {"wall_s": perf_counter()-started, "peak_left_hz": max(left),
            "peak_right_hz": max(right), "final_active": int(sim.spikes.sum()),
            "step_ms": sim.last_step_ms}

if __name__ == "__main__":
    probe = ConnectomeSimulation(CACHE)
    print("motion/efferent overlap", int((probe.motion & probe.motor).sum()))
    print("baseline", trial(stimulated=False))
    print("motion stimulus", trial())
    print("same stimulus, annotated motion inputs silenced", trial(silenced=True))
    print("same stimulus, all edge weights zero", trial(disconnected=True))
