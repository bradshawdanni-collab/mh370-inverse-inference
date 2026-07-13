# L6.1 — Comparative Assessment Record

## Purpose

`ComparativeAssessmentRecord` captures one deterministic structural comparison between two distinct hypothesis identities admitted by one exact L6.0 request.

```text
ComparativeAssessmentRequest
        + permitted hypothesis identities
        + structural comparison relation
        ↓
ComparativeAssessmentRecord
```

## Contract surface

The record preserves:

- the exact `ComparativeAssessmentRequest.request_hash`;
- an ordered left hypothesis identity;
- an ordered right hypothesis identity;
- one explicit structural relation;
- a comparison-rule identifier and version;
- the L6.1 contract version;
- a canonical content-derived `record_hash`.

The public constructor is disabled. Records are created only through `build_comparative_assessment_record`.

## Structural relation values

- `SAME_DISPOSITION`
- `DIFFERENT_DISPOSITION`
- `INDETERMINATE`

These values describe only the structural relation asserted by the named comparison rule. They do not establish truth, preference, plausibility, or physical correctness.

## Validation

The builder rejects:

- non-L6.0 request objects;
- mutable or malformed permitted-hypothesis sets;
- malformed hypothesis hashes;
- self-comparison;
- hypothesis identities outside permitted lineage;
- invalid relation values;
- blank rule identifiers or versions.

Pair order is preserved. Comparing `A` to `B` is a different canonical record from comparing `B` to `A`.

## Deterministic identity

The record hash is computed with `sha256_payload` over:

```text
comparative_record_contract_version
comparative_request_hash
comparison_rule_id
comparison_rule_version
left_hypothesis_id
relation
right_hypothesis_id
```

No clock, UUID, random source, filesystem state, network state, registry state, or persistence authority participates in identity.

## Boundary

L6.1 does not introduce:

- probability or confidence;
- evidence weighting;
- hypothesis ranking;
- Bayesian updating;
- trajectory or drift modelling;
- endpoint, coordinate, or location conclusions;
- search-area recommendations;
- causal authority.

The record is a replayable structural artifact only.
