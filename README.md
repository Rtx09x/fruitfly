# Fruitfly Connectome Lab

An honest, local buildathon demo that runs a simplified leaky integrate-and-fire (LIF) simulation across the **complete connectivity table in this repository** and uses the computed activity to drive a browser visualization and a deliberately simple fly avatar.

## Run

Requires Python 3.10+ and NumPy. The first launch streams the compressed CSVs into a ~68 MB memory-mapped cache and takes about 30 seconds on the reference laptop; later launches reuse it only when source SHA-256 fingerprints match.

**Windows**

```bat
run_windows.bat
```

**macOS / Linux**

```sh
chmod +x run_mac.sh
./run_mac.sh
```

Or: `python -m pip install -r requirements.txt && python run.py`. Open <http://127.0.0.1:8765>. Use `--data /path/to/fruit_fly_brain_dataset`, `--port 9000`, `--no-browser`, or `--rebuild` as needed.

## What actually runs

- 139,255 neurons and all 5,342,446 aggregated directed connections in `connections_princeton.csv.gz` are held in compact memory-mapped arrays. Those edges represent 50,666,648 underlying synapses. No downsampled or synthetic graph is substituted.
- Every integration step gathers current from the prior spike state over the full edge table and accumulates it at postsynaptic neurons.
- Synapse count controls magnitude. Dataset transmitter labels provide the sign: ACh/OCT/DA/SER are treated as excitatory and GABA/GLUT as inhibitory. This is a simplification; receptor-specific effects are unavailable.
- Neurons use a discrete current-based LIF-like update at a documented 5 ms timestep. This lightweight interactive model is **inspired by, not a numerical reproduction of**, Shiu et al.'s published whole-brain LIF model. It omits their alpha-synapse dynamics, delays, refractory period, calibrated membrane units, and validated sensory experiments.
- Manual motion and looming controls inject current into neurons bearing the dataset's `Motion` and `Object` visual subsystem annotations. The mapping and amplitude are assumptions.
- The opt-in webcam adapter computes coarse left/right frame differences locally in the browser and maps them to the same motion controls. It does not classify food, faces, or behavior, and no frames are uploaded.
- The fly avatar's speed is the mean bilateral efferent firing rate and turn is the left/right difference, with fixed gains in `simulation.py`. This is an explicitly heuristic motor decoder, not a validated muscle or behavior circuit.
- The activity view shows a stable sample of 900 neurons at their real x/y coordinates (first coordinate per root, percentile-normalized). Color is computed per-neuron activity. It is not an anatomical parcellation.

The implementation follows the general principle of the published model—spikes alter downstream membrane potential in proportion to signed connectome weight, followed by leak and threshold—described in [Shiu et al., Nature 634, 210–219 (2024)](https://doi.org/10.1038/s41586-024-07763-9). The local filenames and counts are consistent with the [FlyWire v783 connectivity release](https://zenodo.org/records/10676866), but this repository does not include an upstream version manifest. For that reason the app reports exact local file hashes rather than asserting provenance it cannot prove.

## Measured reference run

On the provided Intel i3-1315U / 8 GB Windows laptop with NumPy 2.3.5:

- Cache build: 30.88 s; cache size: 67.53 MB.
- Full-network integration: about 81 ms/step (roughly 12 computational steps/s, or 0.06× real time at a 5 ms model timestep).
- 100-step quiet baseline: peak efferent rate 0 spikes/s.
- Left-heavy motion injection from step 20: peak left efferent rate 0.087 spikes/s versus right 0 in this deterministic seed-1 run.
- The same injected values with annotated motion inputs silenced: peak efferent rate 0 spikes/s.
- The motion/efferent annotation masks overlap at 0 neurons; with identical stimulus and every edge weight zero, peak efferent rate is also 0 spikes/s (2,168 stimulated input neurons were active at the final step).

Run `python benchmark.py` to reproduce four 100-step trials: baseline, stimulus, the same stimulus with annotated motion inputs silenced, and with all edge weights zero. The controls distinguish downstream connectivity effects from a scripted avatar reaction. The script also verifies that annotated motion and efferent masks do not overlap. Results can differ if model parameters or data change.

Run `python -m unittest discover -v` for structural and stepping checks. `node --check fruitfly/static/app.js` performs a JavaScript syntax check.

## Scientific limitations

This is a visualization sandbox, not a digital fly. It does not model morphology, compartmental dynamics, gap junctions, neuromodulation, receptor identity, plasticity, internal state, muscles, biomechanics, learning, emotions, intent, or thought. Connectivity constrains possible signal flow; it does not establish a neuron's function. Baseline activity and stimulus current are modeling choices. A glowing neuron is not evidence of a mental state or a validated circuit.

The reference paper used FlyWire public materialization v630, 127,400 proofread neurons, alpha-synapse dynamics, calibrated electrophysiological parameters, and specific experimentally grounded sensory populations. This demo's local table has 139,255 neurons and appears to be from a later release, so direct comparison of output values would be inappropriate.
