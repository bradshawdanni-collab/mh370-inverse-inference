# Evidence Provenance Contract

## Status

This document defines the bounded **Issue #9A** provenance schema and immutable
record contracts.

It does not yet implement the provenance registry, checksum service, attribution
linkage, SATCOM migration, or final Issue #9 audit. Those remain separately
gated as #9B through #9E.

## Purpose

The provenance layer provides one repository-level identity model for scientific
artifacts without replacing the existing domain source registers, SATCOM
provenance artifacts, observation-admission contracts, or evidence-assembly
contracts.

Existing records remain authoritative within their established boundaries. Later
Issue #9 stages will adapt and link them into these generic contracts rather than
creating a parallel scientific authority.

## Contract version

The initial repository-level contract version is:

```text
PROVENANCE-1
```

The implementation is in:

```text
src/mh370_inverse_inference/provenance/models.py
```

## Artifact identity

Every governed artifact is represented by an exact `ArtifactReference` containing:

- `artifact_id` — stable repository identity;
- `version` — explicit artifact version;
- `sha256` — lowercase SHA-256 digest of the exact artifact bytes.

An artifact reference identifies one exact version only. A later version must use
a distinct version value and digest.

## Artifact kinds

The contract defines three artifact kinds:

```text
SOURCE
DERIVED
VALIDATION
```

`SOURCE` represents an exact retrieved or repository-captured source artifact.
`DERIVED` represents an artifact produced deterministically from one or more exact
input artifacts. `VALIDATION` represents a deterministic validation output.

## Admission lifecycle

The contract defines these explicit states:

```text
PROPOSED
VERIFIED
ADMITTED
REJECTED
SUPERSEDED
```

Issue #9A defines the state vocabulary only. Transition authority and registry
mutation rules are deferred to #9B so state changes remain auditable and do not
become implicit dataclass mutation.

All provenance records are frozen dataclasses.

## Source reference

A `SourceReference` records:

- stable source identity;
- publisher;
- title;
- reference URI;
- canonical UTC retrieval timestamp using `Z` notation;
- licence or documented usage terms;
- exact lowercase SHA-256 content hash.

For a `SOURCE` artifact, the artifact SHA-256 must exactly equal the source
content hash, and no transformation history is permitted.

## Transformation history

Each `TransformationStep` records:

- contiguous `step_index`;
- deterministic operation name;
- exact versioned input artifact references;
- exact output artifact reference;
- implementation reference;
- configuration identifier.

`DERIVED` and `VALIDATION` artifacts must contain a transformation history. The
final transformation output must equal the artifact reference governed by the
record.

No hidden normalization, inferred source substitution, nearest-source lookup, or
network retrieval is part of this contract.

## Uncertainty and limitations

`ArtifactProvenanceRecord` carries ordered uncertainty notes and limitations as
explicit immutable fields. These fields preserve scientific caveats alongside
artifact identity rather than leaving them only in narrative documentation.

Issue #9A does not interpret or score uncertainty.

## Supersession

An artifact in state `SUPERSEDED` must identify a distinct replacement artifact
reference. Other admission states cannot silently carry a supersession target.

Supersession does not delete or rewrite the older artifact identity.

## Validation linkage

`ValidationReportRecord` links:

- stable validation ID and version;
- exact versioned input artifact references;
- exact validation output artifact reference;
- model version;
- configuration ID.

This contract is intentionally generic. Issue #9D will use it to link the
already-admitted seventh-arc fixture and the completed L0.4 validation output
without regenerating either artifact.

## Relationship to existing contracts

The repository already contains domain-specific provenance mechanisms, including:

- SATCOM source registers and frozen provenance artifacts;
- observation source and admission contracts;
- evidence assembly provenance links and exact identity hashes.

Issue #9A does not replace those contracts. It establishes the repository-level
schema that later adapters and registry operations will consume.

## Explicit exclusions

This stage does not add:

- a writable provenance registry;
- file hashing or checksum verification services beyond digest-format validation;
- citation or evidence-use attribution;
- automatic source discovery;
- network retrieval;
- source-authority promotion;
- migration of existing SATCOM records;
- BFO processing;
- aircraft dynamics;
- trajectory inference;
- debris modelling;
- probability or ranking;
- endpoint selection;
- search-area recommendation;
- crash-location claims.

## Issue #9 sequence

```text
#9A provenance schemas and immutable contracts      current
 ↓
#9B checksum verification and local registry
 ↓
#9C attribution and evidence-use linkage
 ↓
#9D SATCOM fixture + L0.4 validation provenance linkage
 ↓
#9E full provenance audit and deterministic replay
 ↓
#5 L1 Aircraft Dynamics and Reachability
```

Aircraft dynamics remains blocked until the complete Issue #9 gate is closed.
