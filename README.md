# Transparent-depth-fusion: analysis records

**Transparent-Object Depth Recovery with Heterogeneous RGB-D Views: An Empirical Study of Observation Gains and Fusion Costs**  
Haoyang Lu and Bin Xu · Hubei University of Science and Technology

[中文说明](README_zh-CN.md) · [Evidence index](docs/RECORD_INDEX.md) · [Data dictionary](docs/DATA_DICTIONARY.md) · [Replaying saved records](docs/REPRODUCTION.md) · [Rights](RIGHTS_AND_LICENSES.md)

This is a scoped research-record package associated with manuscript **B0.9**. Package revision: **public-records-v1**. It contains existing numerical results, evaluation-pair metadata, configuration records, and CPU-only analysis scripts. It is not a new depth-completion method, an accepted/publication-status claim, or a complete training/inference distribution. The package revision is not a GitHub tag or DOI until one is actually created.

## Study

The controlled comparison fixes the calibrated **D435 source → L515 target** direction at 320 × 240 on 2,193 pairs from 11 TransCG scenes. `D` in the saved files means **TDCNet-local**; `FDCT` means **FDCT-local**. The front ends are separately frozen conditions with unmatched training histories, not an equal-budget architecture ranking.

- `S`: target-only prediction.
- `R`: averaging with reprojected raw source depth.
- `P`: averaging with reprojected source prediction; the prespecified candidate.
- `P_rep`: source-prediction replacement where covered; an auxiliary operating point.
- `V`: restricted, in-domain, two-view V-FUSE using binary input validity rather than native confidence maps; seeds 11/29/47.

The records distinguish original outputs and common target-raw upper-bound postprocessing. The postprocessed stage is primary. Each condition has the same 2,193 images and 23,112,023 evaluation pixels.

## Reported findings — copied from the frozen manuscript/records

| Quantity | TDCNet-local | FDCT-local |
|---|---:|---:|
| P versus S, image-averaged MAE reduction | 15.87% | 18.46% |
| P versus R, image-averaged MAE reduction | 10.34% | 10.17% |
| Complete G4 relative tolerance, V-best comparisons | 3/3 met | 0/3 met |
| Original-protocol latency reduction, P relative to V | 20.99–21.65% | 24.72–25.73% |
| Resident-protocol latency reduction, P relative to V | 12.99–13.28% | 5.35–5.88% |

All six resident comparisons fall below the unchanged 15% magnitude requirement. Under FDCT-local, P has about 0.45 mm higher MAE than the three-run V metric mean, while having a lower >50 mm error fraction. The conclusions concern these fixed checkpoints and call protocols, not statistical equivalence, a universally optimal system, the original unrestricted V-FUSE performance, or measured robotic-task benefits.

Sources: [saved accuracy summaries](data/accuracy/sources/summary_all.csv), [best/last G4](data/accuracy/expected/best_last_full_G4.csv), [old/new timing](data/timing/resident/new_vs_legacy.csv).

## Contents

| Directory | Included records |
|---|---|
| `data/accuracy/` | Two per-image CSVs (43,860 rows each), original D/seed-11 history, saved overall/per-scene/LOSO tables, G4 and scene-bootstrap summaries |
| `data/selection/` | Six internal fusion-selection traces and eight FDCT development nodes |
| `data/timing/` | 1,400 original calls; 4,224 resident calls including 1,056 warmups and 3,168 measurements; saved summaries, pairing, schedule and block-state records |
| `data/data_selection/` | Historical 2,498-directory inclusion/exclusion record, 305 excluded entries, preserved archive-member metadata, two-stage reconciliation |
| `data/qualitative_selection/` | Selection rules and numerical example records only; **no images or pixel arrays** |
| `configs/` | Selected recorded training/runtime settings and identities; not turnkey training recipes |
| `analysis/` | Existing best/last analysis, public-input timing replay, synthetic tests, package-integrity checker |
| `docs/` | Scope, provenance, data definitions, replay instructions and mapping to manuscript/supplement |

## Start with an integrity check

Python 3.10 or later:

```bash
python -B analysis/verify_release.py
```

This checks package hashes and saved-record structure. It does not train models, run inference, score pixels, or rerun bootstrap.

Optional existing-record replay commands are documented in [REPRODUCTION.md](docs/REPRODUCTION.md). The best/last script uses the Python standard library. The timing replay also uses NumPy. Both write new outputs only when explicitly invoked; no training environment is included.

## Scope and omissions

The repository does **not** redistribute TransCG RGB/depth/ground truth/masks, Figure 4 image excerpts or NPZ caches, trained weights, full historical per-pixel error arrays, third-party network implementations, manuscript PDFs, author correspondence, or internal review/version archives. Obtain TransCG from its [official project](https://graspnet.net/transcg). See [upstream sources](docs/UPSTREAM_SOURCES.md).

Saved P95/P99 values are retained but cannot be independently reconstructed from per-image sums/counts. Five TDCNet-local historical error arrays lack supplied historical SHA256 values. Saved parameter/BN identities and timing logs do not independently certify all historical forward outputs or resident pixel-output equivalence. The final pair manifest's empty `exclusions` list means zero **additional** exclusions in the later check, not zero early exclusions.

Some configurations contain `LOCAL_PROJECT` path labels: these are sanitized historical locations of files **not supplied here**, not paths to run against. Original-file hashes and all changes are documented in `PUBLIC_FILE_MANIFEST.json` and [RELEASE_SCOPE.md](docs/RELEASE_SCOPE.md). Hash agreement checks the supplied bytes; it is not a trusted timestamp or complete historical-origin certification.

## Citation and licensing

Use [CITATION.cff](CITATION.cff) and identify the actual repository commit/tag you used. No paper DOI, acceptance status, or uncreated release is asserted.

**No blanket reuse license has been selected for this initial record package.** Public inspection is distinct from granting unrestricted modification/redistribution rights. The package does not relabel third-party material as MIT or CC BY. See [RIGHTS_AND_LICENSES.md](RIGHTS_AND_LICENSES.md).
