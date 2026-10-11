# Canned BLS payloads

Hand-written payload fragments shaped like BLS v2 time-series responses.
They are test fixture data, **not** recordings of real BLS responses: the
series IDs are synthetic (`TEST_*`), and real recorded flat-file slices
arrive with milestone M2' (see `docs/ROADMAP.md`), which will document their
source URL and retrieval date alongside the data.

Rules for adding files here:

- Never include real API keys, real payload `registrationkey` values, or
  anything beyond public data fields.
- Hand-written fixtures should stay small and hand-checkable.
- Real recordings must name their retrieval date and request parameters
  (see the etiquette rules in `docs/bls_etiquette.md`).

`flatfile/` holds byte-exact slices cut from the owner-saved real files in
`docs/sample_data/` (PC/PD formats confirmed in `docs/bulk_files.md`); the
slice names keep the canonical upstream filename plus a `.slice` suffix so
`data.ingest.classify_file` maps them the same way. The small CI mapping
slices are the *complete* real files. No slice contains fabricated values;
parser mechanics that lack a real data file yet (CI observations) are
tested with inline text in the test module instead. The slices are the
parser's offline ground truth and double as container-build seed input.
