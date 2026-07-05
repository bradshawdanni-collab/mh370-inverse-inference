# L7 Search Domain Baseline

## Purpose

L7 begins as a deterministic search pipeline. The first slice defines only the bounded scalar domain used by later candidate generators and search engines.

This layer does not generate trajectories, score candidates, optimize, or call L1-L6.

## Baseline algorithm choice

The reference baseline should be deterministic grid or exhaustive enumeration. More advanced methods can be added later as optional engines, but the baseline must remain replayable:

```text
same bounds + same steps + same dimension order = same candidate order
```

## High-dimensional handling

High-dimensional spaces must be handled by explicit dimension records and candidate-count accounting before enumeration. A caller can inspect `candidate_count` before deciding whether a grid is tractable.

The baseline does not hide dimensional explosion. It exposes it directly.

## Repeatable score comparison

L7 search metrics should be derived from stable fields:

- number of dimensions;
- count per dimension;
- total candidate count;
- deterministic dimension order;
- normalized coordinate values;
- later, evaluation count and top-N posterior outputs.

These metrics allow repeatable comparison between search runs without relying on stochastic optimizer behavior.

## Boundaries

This slice excludes:

- trajectory generation;
- candidate scoring;
- posterior ranking;
- heuristic optimization;
- stochastic sampling;
- adaptive search.

Those belong to later L7 slices after the domain contract is stable.
