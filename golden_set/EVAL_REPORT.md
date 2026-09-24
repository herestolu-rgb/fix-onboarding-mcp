# EVAL_REPORT v0.2.0-rag-eval
# Evaluation Report

## Canonical Harness

The canonical evaluation corpus contains 70 cases:

- 25 valid NewOrderSingle cases
- 25 invalid NewOrderSingle cases
- 20 Cancel/Replace edge cases

Current executable harness result:

- Discovered: 70
- Evaluated: 64
- Out of scope: 6
- Unsupported: 0
- Matched: 64
- Mismatched: 0
- Unaccounted: 0

The 6 remaining out-of-scope cases represent contextual policy that is not yet
implemented:

- 3 VENUE_FIRMUP_POLICY cases
- 3 REGULATORY_LEI_POLICY cases

Three VENUE_SIDE_POLICY cases that were previously out of scope are now
evaluated using explicit caller-supplied validation context.

The harness does not infer venue-policy authority from FIX CompID fields or
descriptive corpus metadata. A venue policy is activated only when the case
provides explicit `validation_context`, for example:

    "validation_context": {
      "venue_id": "VENUE_X"
    }

This preserves the distinction between message data and decision authority.

## Contextual Validation Result

The contextual-validation work exposed an important limitation in the previous
green benchmark.

The earlier harness reported:

- Evaluated: 61
- Out of scope: 9
- Matched: 61
- Mismatched: 0

That result was internally consistent, but the three VENUE_SIDE_POLICY cases
were not exercising the newly implemented authority-aware validation path.

Those three cases were moved into executable scope with explicit VENUE_X
validation context. Before the harness supplied that context, the result
intentionally became:

- Evaluated: 64
- Matched: 61
- Mismatched: 3

The harness was then updated to bind only the explicit `validation_context`
provided by the corpus. The resulting evaluation is now 64/64 matched with
zero unexplained mismatches.

This progression demonstrates that matching expected verdicts is not sufficient
evidence of correctness if the system reaches those verdicts under the wrong
authority or assumptions.

## Evaluation Boundary

The current harness evaluates deterministic validation verdicts against the
canonical golden corpus.

Generic FIX protocol validation is evaluated independently of venue policy.

The implemented contextual venue-policy slice currently covers explicit
VENUE_X Side policy. FirmUp policy and regulatory LEI policy remain explicitly
out of scope rather than being inferred or simulated by the generic validator.

The following are not currently implemented or measured:

- RAGAS faithfulness
- retrieval/context precision
- model confidence thresholds
- vector/BM25/RRF retrieval latency

No numerical claims for those metrics should be inferred from this report.

## Data

The canonical corpus is stored under `golden_set/`.