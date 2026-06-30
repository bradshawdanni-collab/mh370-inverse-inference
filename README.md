# MH370 Inverse Inference

A reproducible scientific framework for ranking plausible MH370 impact regions using SATCOM geometry, aircraft dynamics, debris transport, search non-detection, and uncertainty analysis.

## Scope

This repository does **not** claim to locate MH370. It provides a modular, testable pipeline for evaluating competing impact-region hypotheses under explicit assumptions.

## Initial milestone

The first milestone is **L0 SATCOM geometry**: reproduce published BTO-derived arcs and uncertainty bands before adding aircraft dynamics or debris transport.

## Project layout

- `src/mh370_inverse_inference/` — Python package
- `tests/` — automated validation tests
- `docs/` — architecture, assumptions, evidence model, and validation plan
- `data/` — source-bounded data directories with provenance notes
- `notebooks/` — exploratory analyses only; production logic belongs in `src/`

## Development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
ruff check .
black --check .
mypy src
```

## Scientific standard

Outputs should identify:

1. admissible 7th-arc segments,
2. rejected corridor segments,
3. uncertainty bands,
4. sensitivity to assumptions,
5. evidence contribution by layer.

## Status

Repository foundation initialized. No crash-location result is asserted.
