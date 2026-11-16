# Package origin and transformations

Source: the supplied B0.9 source-and-verification ZIP, `IEEE_Sensors_B0.9_源码与核验包.zip`, scientific baseline B0.9. Original manuscript and internal evidence files were not edited. Public-package revision `public-records-v1` was prepared locally on 2026-11-16 for `Yang11544/transparent-depth-fusion`; preparation does not mean a remote upload/tag/release already exists.

## Preserved

Per-image numerical CSVs, saved summary/LOSO/G4 tables (apart from path labels in checkpoint-identity tables), internal selection traces, timing per-call CSVs and result tables, the final pair manifest, and early per-directory exclusions are byte-identical source copies. Original selected-example numbers and selection rules are included without the image caches.

## Sanitized or reorganized

- Private machine path prefixes are replaced by descriptive `LOCAL_PROJECT`, `LOCAL_AUXILIARY_PROJECT`, `LOCAL_HOME` or `LOCAL_BUILD` labels. Numerical values, SHA256 identifiers, scene/view identities and checkpoint selection are not changed.
- The hardware record's GPU UUID is redacted; GPU model, driver, memory and software-version fields remain descriptive recorded information.
- Interactive authorization text and local job-control/context fields are excluded from public protocol subsets. Fixed scientific settings and their source-file hashes are retained. The initial protocol's method names are historical; final analysis uses the supplied alignment and lock records.
- The archive-member inventory retains its field values except local path prefixes and is serialized as compact JSON. It is metadata, not a re-created dataset archive.
- Thirty-two saved block-completion objects are concatenated into one file to keep the public package manageable. No block results are regenerated.
- The best/last analyzer and its five existing synthetic tests are unchanged. Timing calculation functions are unchanged; only the reader/entry point and needed file-I/O helpers are adapted to public paths and CSV exports.
- `source_manifest.json` inside the accuracy input directory is a newly generated **public-input** manifest. It is not labeled as the historical manifest. Full per-file source and public hashes are in `PUBLIC_FILE_MANIFEST.json`.
- Documentation, citation metadata and `analysis/verify_release.py` are new packaging aids, not historical scientific evidence. AI assistance was used to prepare documentation and the public-input wrapper; no new scientific claim or experiment is introduced.

## Excluded from this package

Upstream network/training code with separate rights, TransCG RGB/depth/GT/masks and NPZ image caches, full pixel-error arrays, checkpoints, raw archives, model binaries, manuscript PDFs/TeX/Word, email addresses and correspondence, internal reviews, historical paper versions, editor-facing preparation documents, build logs, and document-font/template files.

The broad historical technical archive contains more than this public package. An omitted item is not represented as publicly available. The manuscript's availability statement must describe this narrower release after its actual upload, rather than claim the internal technical package is fully on GitHub.

## Interpretation boundaries

Recorded timestamps and hashes are not independent trusted timestamp or provenance certificates. File hash consistency is distinct from numerical correctness, and saved numerical consistency is distinct from raw-data/model-output authentication. Scope limits concerning quantiles, missing historical TDCNet error-array hashes and resident output equivalence are unchanged.
