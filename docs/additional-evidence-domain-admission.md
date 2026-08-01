> **Namespace notice (ED1.0):** This document historically used an L5.x label. The canonical namespace is now ED1.0 under the Layer Namespace Registry. Existing contract versions and artifact identities remain unchanged.

# L5.0 Additional Evidence-Domain Admission Contract

## Purpose

This contract defines the common admission boundary for additional MH370 evidence domains before any later integration or fusion step.

Supported initial domains are:

- radar uncertainty;
- debris drift;
- prior search non-detection;
- search coverage.

## Required identity and provenance

Every evidence-domain record requires:

- immutable domain identifier and version;
- source identifier, source version, citation, and SHA-256 content hash;
- ordered transformation history with implementation identity and parameter hashes;
- explicit uncertainty representation, units, method, and optional bounds;
- validation report identifier, version, SHA-256 hash, and disposition;
- explicit admission state;
- deterministic canonical record hash.

An `ADMITTED` record requires a validation disposition of `PASS`.

## Deterministic serialization

The record hash is computed from canonical JSON serialization using sorted keys and compact separators. Reconstructing the same governed record must produce the same SHA-256 value. Any payload or hash modification fails closed.

## Relationship to L3

Admission of an additional evidence domain has no automatic effect on the admitted L3 BTO, BFO, and reachability disposition. Every record is fixed to:

`NONE_UNTIL_GOVERNED_INTEGRATION`

A separate contract, validation gate, and final admission decision are required before any additional domain may influence an integrated result.

## Scope boundary

L5.0 does not:

- fuse evidence domains;
- rank trajectories or hypotheses;
- select endpoints;
- recommend search areas;
- make a crash-location claim.

It establishes only the reusable admission contract that later domain-specific work must satisfy.
