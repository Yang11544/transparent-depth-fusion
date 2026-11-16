# Public evidence map for manuscript B0.9

The manuscript and supplement were prepared with a larger internal technical package. This public subset uses the paths below; it does not reproduce all internal `reproducibility/` paths. Section/table identifiers refer to the B0.9 manuscript and supplement, not to this README.

| Question / paper location | Public location |
|---|---|
| Overall original and postprocessed scores: main Table II, S1/S8 | [saved summary](../data/accuracy/sources/summary_all.csv), [D per-image](../data/accuracy/sources/D_per_image.csv), [FDCT per-image](../data/accuracy/sources/FDCT_per_image.csv) |
| Scene composition and uncertainty: S9/S11, Figs. 1–2 | [D scenes](../data/accuracy/sources/D_saved_per_scene.csv), [FDCT scenes](../data/accuracy/sources/FDCT_saved_per_scene.csv), [scene intervals](../data/accuracy/scene_bootstrap.json), [scene-equal](../data/accuracy/scene_equal.csv) |
| Complete G4 and best/last: main Table III, S2/S10/S17 | [best criterion](../data/accuracy/sources/saved_best_criteria.csv), [full G4](../data/accuracy/expected/best_last_full_G4.csv), [all omissions](../data/accuracy/expected/best_last_LOSO_comparisons.csv), [identity](../data/accuracy/expected/checkpoint_identity.csv) |
| Internal checkpoint selection: IV-B/C, S4/S5/S13 | [selection traces](../data/selection/), [model locks](../data/accuracy/sources/model_lock_record.json), [configurations](../configs/) |
| Original cost: S3/S12, Fig. 3 | [original calls](../data/timing/original/per_call.csv), [summary](../data/timing/original/summary.csv), [intervals](../data/timing/original/bootstrap.json) |
| Resident cost: main Table IV, S18 | [resident calls](../data/timing/resident/per_call.csv), [comparison](../data/timing/resident/new_vs_legacy.csv), [intervals](../data/timing/resident/bootstrap_intervals.csv), [schedule](../data/timing/resident/schedule.json), [block records](../data/timing/resident/block_completion.json) |
| Early 305 exclusions versus later zero additions: IV-A/S6 | [historical directory record](../data/data_selection/source_records/reference/old_inclusion_exclusion.json), [305-row table](../data/data_selection/excluded_305_existing_records.csv), [archive inventory](../data/data_selection/source_records/reference/old_archive_members.json), [final pairs](../data/accuracy/sources/legal_pairs_final.json), [stage counts](../data/data_selection/scene_stage_reconciliation.csv) |
| Figure 4 selection, not frequency: V-G/S16 | [candidate metrics](../data/qualitative_selection/panel_candidate_metrics.csv), [selected examples](../data/qualitative_selection/selected_examples.csv), [fixed selection rule](../data/qualitative_selection/selection_and_display_protocol.json); pixels/caches deliberately omitted |

## Mapping of the original record labels

| Internal label | Public equivalent or explicit omission |
|---|---|
| record-01 | Accuracy source CSVs, saved summaries and scene-bootstrap records above |
| record-02 | `data/selection/` and `data/accuracy/sources/model_lock_record.json` |
| record-03 | `data/timing/timing_panel.json` |
| record-04 | `configs/recorded_environment.json`, public checkpoint identities and manifests; not all internal identity maps |
| record-05 | `data/accuracy/sources/evaluation_alignment.json`, model lock, and selected configuration records; original private command/approval text omitted |
| record-06 | Original label-validation report not distributed in this subset; manuscript S14 retains reported scope, no new label check |
| record-07–13 | Training/loss/augmentation implementation snapshots not redistributed; use recorded settings in `configs/` and manuscript S15, not a claim of runnable training code |
| record-14 | `configs/tdcnet_initial_config.json` |
| record-15–17 | Detailed early completion/recovery/loss-provenance records not duplicated; retained in the internal technical archive |
| record-18–20 | `data/qualitative_selection/` numeric candidate/selection files |
| record-21–25 | Pixel display/cache audit scripts, cache arrays and image provenance archive not distributed; no pixelwise Figure 4 verification is claimed by this package |
| record-26 | `data/accuracy/expected/best_last_full_G4.csv` |
| record-27 | `data/accuracy/expected/best_last_LOSO_comparisons.csv` |
| record-28 | `data/accuracy/expected/checkpoint_identity.csv` (sanitized locator labels) |
| record-29 | Historical sensitivity validation JSON not relabeled as a new validation; outputs and numerical inputs are supplied, local packaging checks are separate |
| record-30 | `analysis/analyze_best_last.py`, byte-identical historical analysis code |
| record-31 | This index and `docs/REPRODUCTION.md` replace the internal working-path guide for public readers |
| record-32 | `data/timing/`, adapted `analysis/analyze_timing.py` and `docs/REPRODUCTION.md`; no model execution code |
| record-33 | `data/data_selection/` plus unchanged `data/accuracy/sources/legal_pairs_final.json` |
