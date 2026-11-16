# Record definitions

## Names, stages and units

`frontend=D` is the fixed TDCNet-local condition; `frontend=FDCT` is the fixed FDCT-local condition. `stage=original` is before the common upper-bound operation. `stage=target_raw_upper_projection` is the prespecified primary stage. Front-end training histories and budgets are unequal.

| Saved method | Paper symbol / role |
|---|---|
| `single` | S: target-only prediction |
| `source_raw_mean` | R: average with reprojected source raw depth |
| `source_prediction_mean` | P: average with reprojected source prediction; prespecified candidate |
| `source_prediction_replace` | P_rep: source-prediction replacement; auxiliary operating point |
| `vfuse_seed11_best`, `vfuse_seed29_best`, `vfuse_seed47_best` | V: internally selected best comparators |
| corresponding `_last` names | completed epoch-30 sensitivity comparators; not replacements selected using test results |

`cohort=reserved11` is a historical record label. Initial confirmation and later predefined follow-up reused the same evaluation set; it does not denote independent test sets for every run.

## Accuracy CSVs

Path: `data/accuracy/sources/{D,FDCT}_per_image.csv`. One row per front end, stage, method and pair. Each file contains 2,193 × 10 × 2 = 43,860 rows. `initial_per_image.csv` repeats part of the early D condition for traceability; do not count it as additional independent data.

| Field | Meaning |
|---|---|
| `pair_id`, `scene`, `view` | Fixed scene/view identity, not an image file supplied by this repository |
| `pixels` | Count in that target image's object/valid-GT evaluation mask |
| `abs_sum_m` | Sum of absolute errors in metres |
| `sq_sum_m2` | Sum of squared errors in square metres |
| `mae_mm` | That image's mean absolute error in millimetres |
| `over50_pixels` | Count with absolute error strictly greater than 0.05 m (50 mm) |

Overall `E_mae_mm` averages image MAEs equally. `Q_rmse_mm` is 1000 times the square root of pooled squared-error sums divided by pooled pixels. `over50_fraction` pools tail counts and pixels. Multiply this fraction by 100 to express percent; differences in percentage points are not relative-percent changes. P95/P99 in saved summary files are recorded pooled nearest-rank quantiles, **not reconstructible from these sums/counts**.

`scene_equal.csv` first averages images within a scene and then weights scenes equally. This differs from the primary image-equal aggregation. LOSO removes a whole scene and recomputes the same primary aggregates.

## G4

The unchanged composite criterion requires P/V MAE and RMSE ratios ≤1.03 overall **and after every scene omission**, plus an overall >50 mm fraction increase ≤0.002 (0.2 percentage points). The tail constraint is global; do not add a new LOSO tail gate. Decisions use unrounded numbers. Meeting G4 is not statistical equivalence or zero MAE cost.

Best comparisons are primary. The completed last-checkpoint evaluation was predefined; the complete best/last G4 reaggregation was a later post-hoc sensitivity analysis. Original-stage G4 rows are diagnostic rather than replacements for the primary postprocessed stage.

## Checkpoint selection

`data/selection/` records internal nodes, not test-based reselection. Six fusion runs completed 30 epochs. The best epochs for D seeds 11/29/47 are 6/6/10; FDCT seeds 11/29/47 are 4/6/4. Their internal-selection scenes 26/30 were held out from fusion fitting but were seen in front-end training. FDCT's eight single-view development nodes select step 30,000.

## Timing

`data/timing/original/per_call.csv`: 1,400 rows, 14 conditions. `first_call=True` (repeat -1) is separate; each condition has 99 subsequent calls. Fields ending `_seconds` are seconds; summaries use milliseconds. Model loading is excluded.

`data/timing/resident/per_call.csv`: 4,224 rows. Filter `phase=measured` for 3,168 rows (396 per condition), and `phase=warmup` for 1,056 rows. Pairing uses frontend, method comparator, round, repeat and pair identity. Saved schedule has 32 separate process blocks. Repetitions do not create independent scenes.

Reduction is `100 * (1 - median(P calls) / median(V calls))` within each protocol. A difference between condition medians differs from a median of paired differences; a ratio of medians differs from a median of per-call ratios. `paired_calls.csv`, `paired_per_pair.csv`, `new_vs_legacy.csv` and `bootstrap_intervals.csv` preserve these distinctions. Intervals condition on the recorded models, 33-pair/11-scene panel, machine and session. Protocol changes do not isolate cache clearing alone. Instrumentation overhead remains inside V latency.

## Data selection

`data/data_selection/source_records/reference/old_inclusion_exclusion.json`: 2,498 directory records; 305 early exclusions for missing required members; 2,193 complete candidates. Its `created_utc` is a saved historical field, not the date this public copy was packaged.

`data/accuracy/sources/legal_pairs_final.json`: the unchanged 2,193-pair manifest. Its empty `exclusions` array means no new failures at the subsequent metadata-intersection/required-file check. Do not add the 305 early exclusions to this later field. `excluded_305_existing_records.csv` is an existing readable extraction, not a replacement for the historical JSON.

`old_archive_members.json` contains **metadata only**, including member paths, CRC values and sizes. Public serialization is compact, with private path prefixes replaced. No archive payload or image pixels are included. Directory CRC zeroes are metadata, not missing-file corruption findings.

## Historical status labels and hashes

`PREPARED_NOT_EXECUTED` or similar states in fixed configuration snapshots describe when that snapshot was made. Actual completed numerical records are stored separately; do not read a historical prepared state as the current paper being unevaluated.

Source hashes identify recorded bytes; missing weights or pixel arrays cannot be authenticated by merely displaying their hashes. `PUBLIC_FILE_MANIFEST.json` distinguishes original hashes from sanitized public hashes and newly generated package files.
