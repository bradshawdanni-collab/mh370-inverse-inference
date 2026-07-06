# L9 Bayesian Evidence Layer

## 1. Purpose

The L9 layer converts independently generated evidence into a deterministic Bayesian posterior profile. The layer does not simulate aircraft motion, ocean drift, SATCOM geometry, or search coverage directly. It receives scalar evidence products from earlier layers and packages them into frozen evidence records.

The core rule is:

```text
same hypotheses + same evidence components -> same posterior profile
```

## 2. Contract Boundary

The fusion contract is implemented by `fuse_evidence`. It accepts:

- a tuple or sequence of `Hypothesis` records;
- a tuple or sequence of `EvidenceComponent` records.

Each `Hypothesis` contains:

- `hypothesis_id`;
- `prior_weight`.

Each posterior output exposes:

- `hypothesis_id`;
- `prior_weight`;
- `joint_log_score`;
- `posterior_probability`;
- evidence contributions.

The contract uses log-space accumulation and stable normalization. It does not expose or require `fuse_evidence_hardened`.

## 3. Evidence Components

An `EvidenceComponent` contains:

- `evidence_type`;
- `source_id`;
- frozen `records`.

Each `EvidenceRecord` maps one `hypothesis_id` to one log-likelihood contribution. Evidence adapters sort hypothesis IDs before emitting records so equivalent mappings produce stable tuple layouts.

## 4. SATCOM Gaussian Adapters

The SATCOM adapter converts abstract scalar BTO and BFO residuals into Gaussian log-likelihoods.

For simulated value `x_sim`, observed value `x_obs`, and channel standard deviation `sigma`:

```text
log L = -log(sigma * sqrt(2*pi)) - 0.5 * ((x_sim - x_obs) / sigma)^2
```

The adapter emits:

- `EvidenceType.BTO` for BTO values;
- `EvidenceType.BFO` for BFO values.

This layer does not compute orbital geometry or Doppler physics. Those values must already be reduced to abstract scalar observations and simulations before entering L9.

## 5. Trajectory-Consistency Adapter

The trajectory adapter converts scalar residuals into Gaussian evidence using the same centered Gaussian form:

```text
log L = -log(sigma_residual * sqrt(2*pi)) - 0.5 * (residual / sigma_residual)^2
```

It emits `EvidenceType.TRAJECTORY_CONSISTENCY`.

The adapter does not integrate trajectories, wrap longitude, sample stochastic paths, or mutate drift state. It only converts already-computed residual magnitudes into evidence records.

## 6. Negative Search Evidence

### 6.1 Role

Negative search evidence models non-detection. It is a finite penalty contribution, not a hard exclusion mask. This preserves continuous posterior support and avoids zeroing the distribution through binary truncation.

### 6.2 Formalization

Each negative search area evaluates the probability that a target would have been encountered and identified along the simulated hypothesis path, `p_detect`. The probability of non-detection is the complement of that value, transformed into log-space:

```text
log L_neg = log(max(1.0 - min(p_detect, p_ceiling), L_min))
```

Where:

- `p_ceiling` is the defensive upper bound preventing singularities from idealized perfect detection claims.
- `L_min` is the linear-scale likelihood floor ensuring overlapping exclusion zones cannot eliminate continuous posterior support.

The production adapter names are:

- `NegativeSearchAdapter`;
- `probability_ceiling`;
- `likelihood_floor`;
- `evaluate_negative_search`.

### 6.3 Constraints

- `p_detect` must be finite and within `[0, 1]`.
- `p_detect = 0.0` maps to `log(1.0) = 0.0`, a neutral identity contribution.
- Detection probability `1.0` is intercepted by `probability_ceiling` and `likelihood_floor`.
- Independent search sectors accumulate additively in log-space through the normal evidence fusion pathway.

## 7. Orchestration Order

The evidence orchestrator is stateless and cache-free. Its merged four-channel order is:

1. `EvidenceType.BTO`
2. `EvidenceType.BFO`
3. `EvidenceType.TRAJECTORY_CONSISTENCY`
4. `EvidenceType.NEGATIVE_SEARCH` when detection probabilities are supplied

If detection probabilities are omitted, the orchestrator preserves the legacy three-channel output.

If detection probabilities are supplied without an injected `NegativeSearchAdapter`, the orchestrator raises a fail-closed `ValueError`.

## 8. Frozen Fixture Policy

The canonical Bayesian fixture is stored under:

```text
tests/fixtures/bayesian/
```

The fixture set contains:

- `case_001.input.json`;
- `case_001.expected.json`;
- `case_001.meta.json`.

The metadata records:

- case ID;
- schema version;
- generator merge commit;
- SHA-256 bindings for fixture files;
- numerical assumptions.

The integration test validates file hashes, hypothesis ID parity, four-channel evidence generation, posterior values, and probability normalization.

## 9. Non-Goals

L9 does not perform:

- aircraft dynamics;
- SATCOM geometry;
- ocean-drift simulation;
- search-area geospatial intersection;
- empirical parameter calibration;
- stochastic sampling;
- dataset loading.

Those responsibilities remain upstream or in future calibration layers.
