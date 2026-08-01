# Layer Namespace Registry

## Purpose

This registry resolves a historical layer-name collision without changing runtime
or scientific behaviour.

The repository already contains a frozen hypothesis-evaluation pipeline under
release `l5-v1.0.0`. Later additional evidence-domain work was described in its
governance history as L5.0 and L5.1, even though it used separate machine contract
versions. Those descriptions collided with the frozen L5 namespace.

## Frozen L5 authority

The original hypothesis release remains authoritative and unchanged:

| Namespace | Frozen contract |
| --- | --- |
| L5.0 | `HypothesisEvaluationRequest` |
| L5.1 | `HypothesisDefinition` |
| L5.2 | `EvidenceHypothesisRelationRecord` |
| L5.3 | `HypothesisEvaluationResult` |
| L5.4 | `HypothesisEvaluationTrace` |
| L5.5 | release freeze |

The release tag remains `l5-v1.0.0`, and its preservation status is
`FROZEN_UNCHANGED`. This registry does not reinterpret, rename, reopen,
supersede, or modify any part of that release.

## Canonical additional-evidence namespace

The additional evidence-domain contracts now use a distinct governance namespace:

| Namespace | Contract | Existing machine version | Status |
| --- | --- | --- | --- |
| ED1.0 | `AdditionalEvidenceDomainAdmission` | `EVIDENCE-DOMAIN-ADMISSION-1` | `ADMITTED` |
| ED1.1 | `EvidenceDomainValidation` | `EVIDENCE-DOMAIN-VALIDATION-1` | `ADMITTED` |

ED1.0 and ED1.1 are canonical governance aliases for the already admitted
additional evidence-domain work. They do not create replacement contracts.

The historical evidence-domain descriptions `L5.0` and `L5.1` are retained only
as `LEGACY_COLLIDING_ALIAS` records. They are non-authoritative and exist solely
for historical traceability.

## Identity preservation

This reconciliation leaves all existing identities intact, including:

- source paths;
- contract-version strings;
- record, report, and replay hashes;
- validation evidence;
- release fixtures and manifests;
- Git history and tags.

The existing implementation files and admitted validation artifact remain in
their current paths. No runtime modules are renamed or rewritten.

## Future namespace rule

Future additional evidence-domain work must use the `ED1.x` namespace.

`ED1.2` is reserved for a future `EvidenceDomainIntegrationRequest`. Reservation
does not constitute implementation or authorization. It permits no evidence
fusion, scoring, weighting, ranking, L3 modification, endpoint selection,
search-area recommendation, or location claim.

## Admission boundary

The registry begins as:

```text
PROPOSED / PENDING_CI
```

It may be promoted only in a separate governance-only change after CI and DX.2
complete successfully.
