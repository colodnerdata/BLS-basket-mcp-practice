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
