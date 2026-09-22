# Fruitfly Connectome Lab

## Latest demo update

The arena now leads the page, with a perspective-projected fly model, a movement trail and camera-relative direction indicator. Camera preview is picture-in-picture at the bottom right; camera and microphone use icon controls. The rotating brain view displays 1,800 sampled neurons in their real 3D coordinates. Rotation is a presentation effect; color reports computed neural activity. Direction is the avatar's heading, not evidence of attraction or avoidance.

The full network now uses SciPy compressed sparse matrix multiplication, retaining all signed connection contributions. A local 100-step trial took about 1.1–1.3 seconds versus approximately 8 seconds previously; speed on your Mac still needs measurement. Pull this branch and rerun the launcher to install the new SciPy dependency, then restart the server and refresh the browser.

Food recognition and sound-specific biological behavior are not implemented. The webcam detects movement and the microphone measures sound energy; neither identifies food or mating calls. Movement continues to come only from simulated motor output.

An honest, local buildathon demo that runs a simplified leaky integrate-and-fire (LIF) simulation across the **complete connectivity table in this repository** and uses the computed activity to drive a browser visualization and a deliberately simple fly avatar.

## Run

Requires Python 3.10+ and NumPy. The first launch streams the compressed CSVs into a ~68 MB memory-mapped cache and takes about 30 seconds on the reference laptop; later launches reuse it only when source SHA-256 fingerprints match.

### Fresh Mac checkout (before the PR is merged)

Install Python 3.10 or newer first, then copy and run exactly:

```sh
git clone -b codex/buildathon-demo https://github.com/Rtx09x/fruitfly.git
cd fruitfly
sh run_mac.sh
```

`run_mac.sh` creates an isolated `.venv`, installs NumPy, builds the local cache from the dataset already tracked in this branch, starts the simulator, and opens <http://127.0.0.1:8765>. The first dependency install and cache build may take a few minutes; later launches are faster. If `python3` is not the desired interpreter, run `FRUITFLY_PYTHON=/full/path/to/python3 sh run_mac.sh`.

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

## Using the demo

The main screen deliberately puts the two immediate interactions first: a large camera/microphone input panel and the animated fly arena. Click **Start camera**, allow camera access, then move a hand across either side of the preview. Click **Start microphone**, allow microphone access, then make a sound. Signal meters confirm local input detection. Neural activity and the fly can respond slowly because this laptop runs the model below biological real time; the yellow timing message reports the actual slowdown. The status distinguishes waiting, detected input with no motor response yet, and computed motor output.

Camera and microphone are independently optional. Manual Sweep/Loom controls below the activity view exercise the same simulation without hardware permissions. Stopping either device releases its tracks/context and clears only that source's current. Closing or refreshing the page also clears device signals through cleanup plus a server-side timeout.

## Troubleshooting

- **Python not found:** install Python 3.10+ and use the `FRUITFLY_PYTHON` override shown above.
- **Missing dataset:** the clone should contain `fruit_fly_brain_dataset/*.csv.gz`. If it does not, confirm you cloned `codex/buildathon-demo` rather than the current default branch.
- **Camera or microphone unavailable/denied:** enable localhost permissions in the browser, ensure no other app owns the device, and press Start again. The error appears beside the relevant button. Manual inputs remain usable.
- **Page says backend disconnected:** leave the terminal running and reload <http://127.0.0.1:8765>. If the port is occupied, use `python run.py --port 9000` inside `.venv` and open that port.
- **Cache error after data changes:** stop the server and run `python run.py --rebuild` inside `.venv`.
- **Slow response:** expected on modest hardware. Watch the real-time factor; input is live, while network propagation advances at the displayed simulation rate.

## What actually runs

- 139,255 neurons and all 5,342,446 aggregated directed connections in `connections_princeton.csv.gz` are held in compact memory-mapped arrays. Those edges represent 50,666,648 underlying synapses. No downsampled or synthetic graph is substituted.
- Every integration step gathers current from the prior spike state over the full edge table and accumulates it at postsynaptic neurons.
- Synapse count controls magnitude. Dataset transmitter labels provide the sign: ACh/OCT/DA/SER are treated as excitatory and GABA/GLUT as inhibitory. This is a simplification; receptor-specific effects are unavailable.
- Neurons use a discrete current-based LIF-like update at a documented 5 ms timestep. This lightweight interactive model is **inspired by, not a numerical reproduction of**, Shiu et al.'s published whole-brain LIF model. It omits their alpha-synapse dynamics, delays, refractory period, calibrated membrane units, and validated sensory experiments.
- Manual motion and looming controls inject current into neurons bearing the dataset's `Motion` and `Object` visual subsystem annotations. The mapping and amplitude are assumptions.
- The opt-in camera adapter computes coarse left/right frame differences locally in the browser and maps them to the same motion controls. It does not classify food, faces, or behavior, and no frames are uploaded.
- The opt-in microphone adapter computes RMS amplitude and a displayed zero-crossing feature locally. RMS becomes current in the 393 neurons explicitly annotated `flow=afferent`, `class=mechanosensory`, `sub_class=auditory`. This is a generic sound-energy adapter, not a reproduction of fly hearing or courtship-song selectivity; audio is never recorded or uploaded.
- Manual, camera, and microphone sources have separate state. Camera motion adds to manual visual input (clamped at 1), while microphone drives only the auditory mask. Per-source sequence numbers reject late requests, and device input expires after 750 ms without a heartbeat.
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
- A deterministic seed-2, 100-step full-strength auditory-input trial uses 393 annotated auditory afferents (0 overlapping efferents) and measured a 0.416 spikes/s peak efferent rate. This is a connectivity response to generic amplitude drive, not evidence of hearing, song recognition, or behavior.

Run `python benchmark.py` to reproduce four 100-step trials: baseline, stimulus, the same stimulus with annotated motion inputs silenced, and with all edge weights zero. The controls distinguish downstream connectivity effects from a scripted avatar reaction. The script also verifies that annotated motion and efferent masks do not overlap. Results can differ if model parameters or data change.

Run `python -m unittest discover -s tests -v` for structural, stepping, input-mixing, and auditory-drive checks. `node --check fruitfly/static/app.js` and `node tests/test_media_features.js` check browser code and deterministic camera/audio feature extraction.

## Scientific limitations

This is a visualization sandbox, not a digital fly. It does not model morphology, compartmental dynamics, gap junctions, neuromodulation, receptor identity, plasticity, internal state, muscles, biomechanics, learning, emotions, intent, or thought. Connectivity constrains possible signal flow; it does not establish a neuron's function. Baseline activity and stimulus current are modeling choices. A glowing neuron is not evidence of a mental state or a validated circuit.

The reference paper used FlyWire public materialization v630, 127,400 proofread neurons, alpha-synapse dynamics, calibrated electrophysiological parameters, and specific experimentally grounded sensory populations. This demo's local table has 139,255 neurons and appears to be from a later release, so direct comparison of output values would be inappropriate.

The code and UI were tested on Windows. The Mac launcher and browser permission flows are implemented but were not exercised on physical Mac hardware. Deterministic camera-frame and audio-sample feature tests pass, but no claim is made that a particular friend's camera/microphone hardware has been verified.
