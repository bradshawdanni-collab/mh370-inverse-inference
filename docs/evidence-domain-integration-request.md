# ED1.2 Evidence-Domain Integration Request

## Status

`PROPOSED` / `PENDING_CI`

ED1.2 defines an immutable deterministic request envelope over exact admitted ED1.0 evidence-domain records and their paired passing ED1.1 validation reports.

It does not produce an integrated evidence result.

## Governing flow

```text
Admitted EvidenceDomainAdmissionRecord(s)
        +
Passing EvidenceDomainValidationReport(s)
        +
Integration policy identity
        ↓
EvidenceDomainIntegrationRequest
```

## Required lineage

A request requires at least two exact evidence-domain records. Every record must:

- be `ADMITTED` under `EVIDENCE-DOMAIN-ADMISSION-1`;
- use a supported evidence-domain type;
- preserve `NONE_UNTIL_GOVERNED_INTEGRATION`;
- preserve the ED1.0 exclusions;
- have one paired ED1.1 validation report;
- have a validation disposition of `PASS` with no failed checks;
- preserve matching record, domain, admission-state, and exclusion identities.

The request rejects duplicate record hashes, validation-report hashes, replay hashes, and duplicate domain identifier/version pairs.

## Canonical fields

The request preserves:

- ordered domain identifiers;
- ordered domain versions;
- ordered domain types;
- ordered ED1.0 record hashes;
- ordered ED1.1 validation-report hashes;
- ordered ED1.1 replay hashes;
- integration-policy identifier and version;
- ED1.0, ED1.1, and ED1.2 contract versions;
- the canonical namespace `ED1.2`;
- the request-level L3 isolation boundary;
- the complete scope-exclusion tuple;
- a deterministic canonical `request_hash`.

`request_hash` is the SHA-256 digest of the canonical JSON payload produced through the repository `sha256_payload` helper. The hash preimage contains every request field except `request_hash`.

## Namespace registry transition

The admitted `LAYER-NAMESPACE-REGISTRY-1` remains unchanged and authoritative while this proposal is under review.

`LAYER-NAMESPACE-REGISTRY-2` proposes ED1.2 as:

- `EvidenceDomainIntegrationRequest`;
- contract version `EVIDENCE-DOMAIN-INTEGRATION-REQUEST-1`;
- status `PROPOSED`;
- authority `NONE_UNTIL_FINAL_ADMISSION`.

The version-2 registry preserves the frozen `l5-v1.0.0` mapping and the admitted ED1.0 and ED1.1 identities exactly. It reserves no namespace beyond ED1.2.

## Scope boundary

ED1.2 does not:

- combine or fuse evidence values;
- calculate weights or scores;
- rank evidence, hypotheses, trajectories, or endpoints;
- modify any L3 disposition;
- select an endpoint or search area;
- make a location claim;
- perform persistence, filesystem, network, registry, or execution actions.

The contract records only which exact admitted and validated evidence-domain identities are permitted to enter a later separately governed integration operation.

## Admission sequence

This implementation and `LAYER-NAMESPACE-REGISTRY-2` remain proposed until CI and DX.2 pass.

Final admission must occur in a separate promotion-only change that records the successful workflow evidence and changes only governance status and evidence fields. No integration-result contract is authorized by ED1.2 admission.
