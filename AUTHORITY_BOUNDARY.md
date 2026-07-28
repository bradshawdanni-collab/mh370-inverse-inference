# MH370 Inverse-Inference Authority Boundary

## Primary role

`mh370-inverse-inference` is a bounded domain application for evaluating competing MH370 impact-region hypotheses under explicit assumptions and uncertainty.

It is authoritative only for repository-local domain assumptions, transforms, validation tests, uncertainty treatment, and comparative inference outputs.

## Canonical upstream

```text
repository: bradshawdanni-collab/aurum-v-kernel
version:    1.0.1
commit:     7f442326f37554aa34b91474648d8406ba99aa5b
```

AURUM-V kernel semantics govern admissibility states, invariants, state transitions, refusal semantics, and execution authority.

## Explicit non-authority

This repository does not:

- assert that it has located MH370;
- issue authoritative accident findings;
- redefine AURUM-V kernel states or invariants;
- weaken a kernel denial in order to preserve a domain hypothesis;
- create execution authority absent from the pinned kernel;
- independently certify its own conclusions.

## Domain rule

A domain test failure, missing evidence, or unresolved uncertainty must be handled within the domain evidence model. It must not be repaired by weakening the upstream governance contract.

Scientific outputs remain hypothesis-ranking or evidence-comparison products unless separately established by competent external authorities.
