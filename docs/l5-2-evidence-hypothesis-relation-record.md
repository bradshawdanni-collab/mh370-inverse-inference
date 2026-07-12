# L5.2 — Evidence-to-hypothesis relation record

L5.2 defines an immutable deterministic record that binds one permitted claim identity to one exact L5.1 hypothesis definition.

## Contract flow

```text
NeutralDerivedClaim identity
    + HypothesisDefinition
    -> EvidenceHypothesisRelationRecord
```

The record captures only whether the claim structurally supports or contradicts the hypothesis. It does not evaluate the hypothesis or alter the L5.0 request envelope.

## Contract fields

- `hypothesis_id`
- `hypothesis_definition_hash`
- `claim_hash`
- `relation_type`
- `relation_rule_id`
- `relation_rule_version`
- `relation_contract_version`
- `record_hash`

The contract version is `L5.2`.

## Structural relation types

- `SUPPORTS`
- `CONTRADICTS`

These values encode direction only. They do not encode magnitude, preference, or comparative merit.

## Canonical identity

`record_hash` is the SHA-256 digest of the canonical payload produced through the repository `sha256_payload` helper. The hash preimage contains every contract field except `record_hash`.

The record preserves both identities from the supplied hypothesis definition:

```text
hypothesis_id == hypothesis_definition_hash
```

## Lineage boundary

The controlled factory accepts an exact `HypothesisDefinition`, one claim hash, and an immutable permitted-claim set. Construction fails when the claim hash is malformed or outside the supplied lineage.

The module performs no authority lookup, reconstruction, external access, or runtime enrichment.

## Deferred work

L5.2 does not produce an evaluation result. Deterministic hypothesis evaluation remains deferred to L5.3, and trace construction remains deferred to L5.4.
