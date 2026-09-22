import json
import time
import unittest
from pathlib import Path
import numpy as np
from fruitfly.simulation import ConnectomeSimulation


class SimulationTests(unittest.TestCase):
    def test_sparse_current_matches_original(self):
        sim = ConnectomeSimulation(Path("fruit_fly_brain_dataset/cache"), seed=1)
        spikes = np.random.default_rng(3).integers(0, 2, len(sim.v)).astype(np.float32)
        reference = np.bincount(sim.post, weights=sim.weight * spikes[sim.pre], minlength=len(sim.v))
        np.testing.assert_allclose(sim.connectivity @ spikes, reference, atol=1e-4)

    def test_real_cache_is_complete_and_steps(self):
        cache = Path("fruit_fly_brain_dataset/cache")
        if not cache.exists(): self.skipTest("build cache first")
        manifest = json.loads((cache / "manifest.json").read_text())
        self.assertEqual(manifest["neurons"], len(np.load(cache / "root_ids.npy", mmap_mode="r")))
        self.assertEqual(manifest["edges"], len(np.load(cache / "pre.npy", mmap_mode="r")))
        self.assertEqual(manifest["unmapped_edges"], 0)
        sim = ConnectomeSimulation(cache, seed=1); sim.step(); state = sim.state()
        self.assertEqual(state["tick"], 1)
        self.assertEqual(len(state["points"]), 1800)
        self.assertEqual(state["dt_ms"], 5.0)
        self.assertGreater(int(sim.auditory.sum()), 0)
        self.assertEqual(int((sim.auditory & sim.motor).sum()), 0)

    def test_source_mixing_and_auditory_drive(self):
        cache = Path("fruit_fly_brain_dataset/cache")
        if not cache.exists(): self.skipTest("build cache first")
        sim = ConnectomeSimulation(cache, seed=1)
        sim.stimulus.update(manual_left=.4, camera_left=.3, audio=1.0)
        self.assertAlmostEqual(sim.state()["stimulus"]["total_left"], .7)
        sim.stimulus.update(manual_left=0, camera_left=0)
        sim.device_updated["audio"] = time.monotonic()
        sim.step()
        self.assertGreater(float(sim.v[sim.auditory].mean()), float(sim.v[~sim.auditory].mean()))
        sim.stimulus["audio"] = 0.0
        self.assertEqual(sim.state()["stimulus"]["audio"], 0.0)


if __name__ == "__main__": unittest.main()
