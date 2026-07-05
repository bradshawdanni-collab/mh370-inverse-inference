# Deterministic CI Hygiene

This repository enforces software-level determinism so that data processing layers, test evaluations, and fixture-backed pipeline behavior remain repeatable across environments and time.

The goal is to keep the execution pipeline close to a pure function: identical repository state and identical declared inputs should produce identical observable outputs.

## Enforced environment primitives

The CI environment neutralizes common runtime drift through `.github/workflows/ci.yml`:

- `TZ=UTC` removes timezone-dependent parsing and formatting differences.
- `LANG=C.UTF-8` and `LC_ALL=C.UTF-8` stabilize locale-sensitive sorting, regex behavior, and byte-stream interpretation.
- `SOURCE_DATE_EPOCH` is set to the UNIX timestamp of the checked-out commit. Build tools and packaging steps that honor this variable should use it instead of the wall clock.

## Coding policies

### Lexicographical input sorting

Filesystem traversal order is not a stable data contract.

Never process raw glob, directory, or filesystem iteration order directly. Sort paths, candidate identifiers, fixture names, and generated record keys before using them as ordered inputs.

```python
# Invalid
for path in glob.glob("data/layers/*.parquet"):
    process(path)

# Valid
for path in sorted(glob.glob("data/layers/*.parquet")):
    process(path)
```

### Explicit pseudo-random seeds

Any stochastic test, fixture generator, randomized search, or simulation must receive an explicit seed through code, configuration, or the fixture metadata.

Acceptable examples include:

```python
rng = numpy.random.default_rng(seed=42)
```

or a fixture metadata field such as:

```json
{"seed": 42}
```

Undeclared randomness is not part of the repository contract.

## Escalation policy

Hardware-level controls are escalation-only. The default CI pipeline does not use cycle-accurate emulation, ASLR changes, CPU pinning, or single-core enforcement.

Escalate only after a reproducibility gap is demonstrated from the same commit under the same software environment, such as divergent fixture hashes or unexplained numeric drift.

## Merge checklist

Before merging changes that affect deterministic execution:

1. Confirm the test suite passes under UTC and `C.UTF-8` locale.
2. Confirm any file collection used as ordered input is explicitly sorted.
3. Confirm any stochastic behavior has an explicit seed.
4. Confirm any fixture output change is intentional and documented.
