> **Namespace notice (ED1.1):** This document historically used an L5.x label. The canonical namespace is now ED1.1 under the Layer Namespace Registry. Existing contract versions and artifact identities remain unchanged.

# Additional Evidence-Domain Validation and Deterministic Replay

## Purpose

L5.1 independently validates records created under the L5.0 additional evidence-domain admission contract.

The validator verifies source identity and citation completeness, SHA-256 syntax, contiguous transformation ordering, uncertainty representation, validation-report identity, admission-state rules, canonical record hashing, preservation of `NONE_UNTIL_GOVERNED_INTEGRATION`, and deterministic replay.

## Representative domains

The validation gate covers:

- radar uncertainty;
- debris drift;
- prior search non-detection;
- search coverage.

Each representative record is validated independently and deterministically. A successful validation report has disposition `PASS`, no failed checks, and stable replay and report hashes.

## Admission boundary

The validation artifact remains `PROPOSED` / `PENDING_CI` until CI and DX.2 pass. Final promotion to `ADMITTED` / `FINAL_ADMISSION_REVIEW_PASS` must occur in a separate governance change.

## Scope exclusions

L5.1 does not:

- fuse evidence domains;
- rank trajectories or hypotheses;
- select endpoints;
- recommend search areas;
- make a location claim;
- alter L3 automatically.

Any integration effect requires a separately governed contract.
