# L2.3 Evidence Registration and Release Identity

L2.3 is the deterministic release gate between validated evidence and downstream inference.

```text
L2.0 admits observations.
L2.1 assembles evidence.
L2.2 validates assembled evidence.
L2.3 registers validated evidence for downstream release.
Later layers interpret it.
```

## Core invariant

Evidence that is not represented by a `RegisteredEvidenceRecord` is not admissible to downstream inference.

Rejected, quarantined, or unregistered artifacts may still exist for audit. Registration grants downstream authority; it does not define repository existence.

## Registration predicate

Registration succeeds only when all of the following are true:

- the L2.2 result status is `VALID`;
- the L2.2 reason set is exactly `OK`;
- the evidence record exists;
- the evidence-record hash matches the frozen expected identity;
- the complete validation-result hash matches the supplied validation identity;
- the L2.2 output and operation hashes are internally consistent;
- the expected registration contract is `L2.3`.

L2.3 verifies the proof already produced by L2.2. It does not rerun observation admission, evidence assembly, or evidence validation.

## Content-addressed identity

The authoritative registry identity is:

```python
registry_evidence_id = sha256_payload(
    {
        "evidence_record": evidence_record.to_payload(),
        "registration_contract_version": "L2.3",
        "validation_operation_hash": validation_result.op_signature_hash,
        "validation_output_hash": validation_result.output_hash,
    }
)
```

Wall-clock timestamps, mutable aliases, database sequence numbers, and lifecycle state do not participate in this identity.

Repeated registration of the same canonical inputs therefore produces the same result and the same `registry_evidence_id`.

## Registered release record

`RegisteredEvidenceRecord` preserves:

- the registry evidence identity;
- the L2.1 evidence identity;
- the originating observation and source identities;
- the canonical evidence hash;
- the complete L2.2 validation-result hash;
- the L2.2 output hash;
- the L2.2 operation-signature hash;
- the L2.3 contract version.

Downstream interfaces should accept `RegisteredEvidenceRecord`, not raw `EvidenceRecord` or `EvidenceValidationResult` objects.

## Failure behavior

Registration fails closed with deterministic reason ordering for:

- non-valid L2.2 outcomes;
- missing evidence records;
- contract mismatch;
- evidence identity mismatch;
- validation identity mismatch;
- internally inconsistent L2.2 proof hashes.

A rejected registration result never includes a registered record.

## Explicit exclusions

L2.3 does not provide:

- persistent registry storage;
- cryptographic signatures or CI attestations;
- Merkle roots or inclusion proofs;
- deprecation, supersession, or lifecycle mutation;
- wall-clock registration identity;
- likelihoods, posterior inference, trajectory ranking, drift analysis, endpoint interpretation, or crash-location interpretation.

Those concerns require separate contracts after the deterministic release identity is frozen.
