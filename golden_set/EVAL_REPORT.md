# EVAL_REPORT v0.2.0-rag-eval

# Evaluation Report

## Canonical Harness

The canonical evaluation corpus contains 70 cases:

- 25 valid NewOrderSingle cases
- 25 invalid NewOrderSingle cases
- 20 Cancel/Replace edge cases

Current executable harness result:

- Discovered: 70
- Evaluated: 61
- Out of scope: 9
- Unsupported: 0
- Matched: 61
- Mismatched: 0
- Unaccounted: 0

The 9 out-of-scope cases represent venue-specific or regulatory policy that is
intentionally not enforced by the generic deterministic validator.

## Evaluation Boundary

The current harness evaluates deterministic validation verdicts against the
canonical golden corpus.

The following are not currently implemented or measured:

- RAGAS faithfulness
- retrieval/context precision
- model confidence thresholds
- vector/BM25/RRF retrieval latency

No numerical claims for those metrics should be inferred from this report.

## Data

The canonical corpus is stored under `golden_set/`.