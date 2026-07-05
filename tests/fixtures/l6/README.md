# L6 Frozen Synthetic Fixture Governance

## Purpose

This directory will contain the canonical synthetic fixture used to verify the full inference chain:

```text
L1-L5 deterministic outputs
    -> L6 evidence
    -> likelihoods
    -> posterior probabilities
    -> ranked trajectories
```

The fixture is a versioned test artifact. It must not be treated as anonymous sample data.

## Planned files

```text
case_001.input.json
case_001.expected.json
case_001.meta.json
generate_case_001.py
```

## Required metadata

`case_001.meta.json` must record:

- stable fixture ID;
- fixture version;
- purpose and behavior exercised;
- generator path and generator version;
- random seed, or an explicit statement that no randomness is used;
- creation date;
- source commit;
- input contract version;
- expected-output contract version;
- numerical tolerances;
- assumptions and known limitations;
- reason for the most recent regeneration.

## Required invariants

The fixture test must verify:

- all deterministic input identifiers are stable;
- evidence records are finite and valid;
- likelihoods are finite;
- posterior probabilities are finite and non-negative;
- posterior probabilities sum to one within the declared tolerance;
- zero-prior hypotheses remain zero;
- ranking is deterministic;
- the expected winning trajectory is unchanged;
- rerunning the generator with the recorded inputs produces the same fixture assets.

## Update policy

Regenerate the fixture only when:

- a layer contract changes;
- the inference method changes;
- a verified bug fix changes the correct expected output;
- the fixture no longer exercises the intended behavior.

Do not regenerate it for formatting changes, refactors that preserve behavior, dependency noise, or unexplained CI drift.

Every update must include:

1. regenerated input, expected-output, and metadata assets;
2. the generator change, when applicable;
3. a review note explaining why the old expected output is no longer correct;
4. passing unit, contract, integration, and frozen-fixture tests.

## Shared test setup discipline

Shared setup must not introduce hidden state or order dependence.

Rules:

- use immutable records where practical;
- return fresh mutable objects from fixtures for every test;
- never mutate module-level fixture data;
- do not cache results unless cache state is explicitly reset;
- avoid environment, clock, network, filesystem, or random dependencies unless injected and recorded;
- use a fixed seed when randomness is required;
- ensure tests pass when run individually, in reverse order, and with randomized order where supported.

## Side-effect detection

The future fixture suite should include checks that:

- input objects are unchanged after evaluation;
- repeated evaluation produces identical output;
- evaluation order does not affect results;
- one test cannot alter another test's fixture state;
- no undeclared files are created;
- no global configuration is modified.

A failure of any side-effect check invalidates the fixture run even when the ranked output is numerically correct.
