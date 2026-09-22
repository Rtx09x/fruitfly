import json
import unittest
from pathlib import Path
import numpy as np
from fruitfly.simulation import ConnectomeSimulation


class SimulationTests(unittest.TestCase):
    def test_real_cache_is_complete_and_steps(self):
        cache = Path("fruit_fly_brain_dataset/cache")
        if not cache.exists(): self.skipTest("build cache first")
        manifest = json.loads((cache / "manifest.json").read_text())
        self.assertEqual(manifest["neurons"], len(np.load(cache / "root_ids.npy", mmap_mode="r")))
        self.assertEqual(manifest["edges"], len(np.load(cache / "pre.npy", mmap_mode="r")))
        self.assertEqual(manifest["unmapped_edges"], 0)
        sim = ConnectomeSimulation(cache, seed=1); sim.step(); state = sim.state()
        self.assertEqual(state["tick"], 1)
        self.assertEqual(len(state["points"]), 900)
        self.assertEqual(state["dt_ms"], 5.0)


if __name__ == "__main__": unittest.main()
