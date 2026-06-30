# Architecture

## Causal structure

```text
Hypothesis
  -> Aircraft state
      -> SATCOM observations
      -> Flight constraints
      -> Impact state
          -> Search non-detection
          -> Debris item states
              -> Recovery observations
```

## Module boundaries

- `satcom`: BTO/BFO geometry and measurement models.
- `aircraft`: performance envelopes and reachability.
- `transport`: Eulerian current, Stokes drift, windage, and coastal transport.
- `debris`: per-item physical state and recovery likelihoods.
- `search`: probabilistic non-detection.
- `bayes`: posterior assembly and hypothesis comparison.
- `visualization`: maps and uncertainty summaries.

Each module must be independently testable before joint inference.
