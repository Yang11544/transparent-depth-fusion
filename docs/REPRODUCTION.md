# Inspecting and optionally replaying saved analyses

## Scope

This package supports analysis of saved records. It cannot perform model training, neural inference, raw-pixel scoring, exact P95/P99 reconstruction, physical-distance certification, or robot-task evaluation. No raw data, model weights, model implementation repositories, or full pixel arrays are supplied. The timing analyzer replays a past call log; it does not benchmark this computer.

## 1. Verify the downloaded package

From the repository root, with Python 3.10 or later:

```bash
python -B analysis/verify_release.py
```

This is a file-integrity and structural check, not a numerical reanalysis. It reads SHA256 hashes, table keys, saved counts, and manifests. No experiment, scoring, or bootstrap is run.

## 2. Existing synthetic unit tests (no experiment samples)

```bash
python -B analysis/test_sensitivity.py
```

The five tests use small synthetic values to check weighting, G4 tails and boundary behavior. They do not validate the original training runs.

## 3. Optional replay of the saved best/last analysis

The script is byte-identical to the existing record-only analyzer; its public input manifest is regenerated for the sanitized files. Do not substitute other test scenes or checkpoints.

```bash
python -B analysis/analyze_best_last.py --sources data/accuracy/sources --out local_outputs/best_last
```

The output directory must not already contain files and must not be inside `data/accuracy/sources`. This reads existing per-image scores, checks units and sample identity, and recomputes overall, per-scene, LOSO and G4 summaries. It does not read images or weights, rerun predictions, recalculate quantiles, or run bootstrap. `data/accuracy/expected/` contains the historical saved outputs for comparison. Checkpoint path labels in public identity outputs are sanitized locators, not available model files.

## 4. Optional replay of saved resident timing

```bash
python -m pip install -r requirements.txt
python -B analysis/analyze_timing.py --run-dir data/timing/resident --out local_outputs/resident_replay
```

This reproduces calculations from the saved per-call records, including the existing 2,000-replicate paired scene bootstrap. **It creates no new call measurements.** It uses recorded model-state hashes but does not load models or independently prove historical execution identity. Never mix original absolute times with resident measurements.

The calculation functions are unchanged from the existing timing analyzer. Its reader was adapted to the public exported CSV and combined saved block-completion JSON, instead of relying on private historical run directories. The adaptation is recorded in [timing_reader_changes.diff](timing_reader_changes.diff). It writes a new directory and does not replace saved result CSVs.

## What was actually tested while packaging

Package hashes, required-file availability, saved schema/row counts and pair keys, Python syntax, `--help` entry points, and the existing synthetic unit tests were checked. The archived-data reaggregation and bootstrap commands above were **not run during this packaging task**. Readers can execute them explicitly as a separate saved-record analysis. All numerical results in `data/` are copied from the B0.9 evidence bundle, not newly obtained in the release preparation.

Exact results of local packaging checks are summarized in `PACKAGE_VALIDATION.json`. That report is not peer review, journal acceptance, or independent reproduction from raw experimental data.
