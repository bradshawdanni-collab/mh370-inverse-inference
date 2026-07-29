# Provenance Audit and Deterministic Replay

## Status

This document defines the final Issue #9E gate over the repository-level provenance work completed in #9A through #9D.

The audit is local, deterministic, fail-closed, and bounded to exact checked-in artifact identities. It does not retrieve external sources, regenerate admitted SATCOM artifacts, or reinterpret domain-specific scientific authority.

## What is audited

The audit confirms the exact provenance chain for:

- immutable provenance contracts;
- checksum and registry contracts;
- attribution snapshots;
- the admitted seventh-arc fixture;
- the L0.4 validation-output identity;
- the exact `ValidationReportRecord`;
- retrieved, cited, and used evidence records;
- registry and attribution snapshot hashes.

## Deterministic replay boundary

Replay reconstructs the provenance identity chain in this order:

```text
Frozen artifact references
        ↓
Artifact provenance records
        ↓
Canonical registry snapshot
        ↓
ValidationReportRecord
        ↓
Retrieved / cited / used records
        ↓
Canonical attribution snapshot
        ↓
Final linkage payload
        ↓
Replay digest
```

The replay hashes canonical payloads only. It does not rerun the surface-locus solver, reload external scientific sources, rewrite the admitted fixture, or create a second copy of the L0.4 validation output.

Identical checked-in identities must reproduce identical registry, attribution, linkage, step, and final replay hashes.

## Fail-closed behaviour

A missing exact artifact, mismatched digest, incorrect admission state, broken validation input/output link, invalid snapshot binding, or altered replay step produces failure. The audit does not downgrade these conditions to warnings.

## SATCOM identities

```text
fixture SHA-256
3ae049f3de7383a433cb8b0b2e1a83e503da99d0dd6e0e96bb9cc39b530cd5a7

validation-output SHA-256
6d4b73fd19afaf3aabec46520551be9d05ab89aa25db11126cad747103452982

model version
l0.4-wgs84-v1

configuration
sequence-index-aligned-geodesic-v1

sample count
176
```

## Authority boundaries

The generic provenance audit does not replace the existing SATCOM source registers, final admission review, transform records, fixture sampling contract, or Issue #7 validation implementation. Those artifacts remain authoritative within their established domains.

The #9E layer verifies that their exact identities are linked consistently through the repository-level registry, validation, attribution, and replay contracts.

## Machine-readable artifact

The frozen audit artifact is:

```text
data/provenance/issue_9_full_audit_v1.json
```

It uses canonical JSON, sorted keys, UTF-8, no generated UUID, no uncontrolled timestamp, and a final LF newline.

## Explicit exclusions

The audit introduces no:

- BFO inversion;
- aircraft dynamics;
- trajectory generation;
- debris modelling;
- probability or ranking;
- endpoint selection;
- search-area recommendation;
- crash-location claim.

## Gate relationship

Issue #5 remains blocked until #9E passes, is merged, and Issue #9 is formally closed. Only then can L1 Aircraft Dynamics and Reachability become the active implementation milestone.
