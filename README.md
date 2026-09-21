# FIX Onboarding Validator - MCP Server

A prototype FIX onboarding validation system combining deterministic FIX
validation, an MCP interface, LangGraph workflow components, and an executable
golden-set evaluation harness.

The project is focused on building practical, explainable AI-assisted tooling
for real electronic-trading and FIX onboarding workflows.

---

## Current Architecture & Validation Flow

![FIX Onboarding MCP - Thin Alignment Architecture](assets/fix-onboarding-mcp-thin-alignment.png)

The diagram above represents the current aligned architecture and the direction
of the next contextual-validation phase.

The executable foundation is deterministic FIX validation exposed through MCP,
with explicit **PASS / FAIL / ESCALATE** verdict semantics.

Venue-specific and regulatory policy is deliberately kept outside the generic
validator where authoritative context is required.

The contextual/RAG layer shown on the right is **planned capability** and is
not currently implemented.

---

## Current Implementation

### Deterministic FIX Validation

The validator currently supports deterministic validation for selected FIX
message workflows, including:

- NewOrderSingle (`35=D`)
- ExecutionReport (`35=8`)
- Cancel/Replace (`35=G`) contextual validation
- FIX delimiters using SOH, pipe, or caret input
- explicit PASS / FAIL / ESCALATE verdict semantics

Generic FIX protocol validity is intentionally separated from venue-specific
and regulatory policy.

For example, standard FIX Side values are not rejected simply because an
individual venue may permit only a subset of those values. Venue-specific
restrictions belong in a contextual policy layer rather than the generic FIX
validator.

### Verdict Semantics

The current validation model distinguishes between:

- **PASS** — deterministic evidence establishes validity
- **FAIL** — deterministic evidence establishes a validation failure
- **ESCALATE** — authoritative context is required before PASS or FAIL can be established

`OUT_OF_SCOPE` is separate from runtime validation verdicts. It is used by the
evaluation harness for cases requiring venue-specific or regulatory policy
that is intentionally outside the authority of the generic validator.

---

## MCP Interface

`mcp_server.py` exposes validation functionality through the Model Context
Protocol.

The MCP interface retains the existing boolean `valid` result for backward
compatibility while adding an explicit `verdict`.

The invariant is:

- PASS → `valid = true`
- FAIL → `valid = false`
- ESCALATE → `valid = false`

This provides a simple interface for future tools, workflows and AI agents
without weakening the deterministic validation boundary.

---

## LangGraph

`langgraph_agent.py` and `langgraph_agent_with_llm.py` provide lightweight
LangGraph workflow prototypes.

The LLM-enhanced workflow currently attempts a local Ollama request using the
`llama3.2` model for error explanation.

If Ollama is unavailable, the workflow falls back to a deterministic
explanation.

This is a prototype workflow, **not a production-ready multi-provider agent**.

---

## Evaluation

The canonical evaluation corpus is stored under `golden_set/` and currently
contains **70 corpus files**.

Current executable harness result:

- **Discovered:** 70
- **Evaluated:** 61
- **Out of scope:** 9
- **Unsupported:** 0
- **Matched:** 61
- **Mismatched:** 0
- **Unaccounted:** 0

The 9 out-of-scope cases represent venue-specific or regulatory policy that is
intentionally not enforced by the generic deterministic validator.

The corpus contains parametrically repeated cases, so **70 corpus files should
not be interpreted as 70 independent validation scenarios**. Expanding
distinct scenario and decision-boundary coverage is part of the next
evaluation phase.

This distinction is intentional: corpus size and decision-boundary coverage
are different measurements.

Run the evaluation harness with:

    python -m eval.harness

Run the complete unit-test suite with:

    python -m unittest discover -v

Current local verification:

- **30/30 tests passing**

---

## Evaluation Philosophy

The alignment work on this project reinforced an important engineering
principle:

> A green benchmark does not necessarily mean correct software.

An implementation, its unit tests and its golden dataset can all agree while
sharing the same incorrect assumption.

One example encountered during development involved FIX Tag 54 (`Side`).

The generic validator originally treated only a narrow subset of Side values
as valid. Review against FIX semantics showed that the standard Side code set
is broader.

A venue may restrict that standard set, but such a restriction is **venue
policy**, not generic FIX protocol validity.

The implementation and evaluation corpus were therefore aligned to the FIX
semantics rather than changing the software merely to satisfy the existing
benchmark.

---

## RAG Status

`rag/fix_spec_rag.py` is currently a scaffold for a future contextual
retrieval layer.

The repository does **not currently implement or measure**:

- vector retrieval
- BM25 or reciprocal-rank fusion (RRF)
- Qdrant
- CrossEncoder reranking
- RAGAS faithfulness
- retrieval/context precision
- model confidence thresholds
- retrieval latency benchmarks

These remain planned architecture rather than current evaluation results.

No numerical RAG, confidence or retrieval-performance claims should be
inferred from the current repository.

---

## Contextual / RAG Architecture - Design Direction

The diagram below is retained as an **architecture design artifact** from the
earlier RAG evaluation design.

It represents the intended direction for a richer contextual validation layer
and **should not be interpreted as evidence that all depicted components are
currently implemented**.

![Future RAG architecture design](fix-onboarding-mcp_v0.2.0_RAG_EVAL.jpg)

The value of retaining this design is to show the architectural direction while
keeping a clear distinction between:

**what is implemented → what is scaffolded → what is planned.**

---

## Planned Contextual Validation

Future work can introduce an evidence-backed contextual layer for:

- FIX specification retrieval
- venue-specific onboarding profiles
- regulatory rule profiles
- original-order and workflow context
- hybrid retrieval and reranking
- context-grounded explanations
- measured RAG evaluation

This layer is intended to address situations where deterministic inspection of
a FIX message alone is insufficient to establish the correct outcome.

For example:

    FIX message
         |
         v
    Deterministic Validator
         |
         +---- PASS
         |
         +---- FAIL
         |
         +---- ESCALATE
                  |
                  v
         Authoritative Context
         /       |        \
      FIX      Venue    Regulatory
      Spec     Policy     Rules
                  |
                  v
         Contextual Validation

Future capabilities should be introduced with executable tests and measured
evaluation rather than placeholder metrics.

---

## Multi-Model Engineering Approach

Development of the project also uses multiple AI systems in complementary
engineering roles rather than treating them as competing sources of a single
answer.

The workflow has included AI-assisted:

- implementation
- architecture review
- debugging
- adversarial review
- evaluation review
- artifact verification

The important principle is that model agreement is **not** treated as evidence
by itself.

Where models disagree, the disagreement is used to expose assumptions for
further investigation.

Domain knowledge, authoritative specifications, executable tests and
engineering judgement remain the final basis for accepting changes into the
repository.

A simplified development loop is:

    AI-assisted implementation
              |
              v
      Architecture review
              |
              v
       Independent review
              |
              v
     Adversarial verification
              |
              v
       Executable evidence
              |
              v
     Human / domain decision

This approach is particularly useful in FIX and electronic-trading systems,
where apparently small semantic assumptions can materially change validation
behaviour.

---

## Engineering Principles

The project currently follows several principles that emerged from the
alignment work:

1. **A green benchmark does not necessarily mean correct software.**
2. **Multiple models agreeing does not constitute evidence if they share the
   same assumptions.**
3. **Architecture intent is not implementation evidence.**
4. **Generic FIX semantics should not be conflated with venue policy.**
5. **A benchmark should expose the boundary of the system rather than pressure
   the implementation into pretending that boundary does not exist.**
6. **Evaluation metrics should only be presented as measured when an
   executable process actually produced them.**

---

## Project Structure

    fix-onboarding-mcp/
        assets/
            fix-onboarding-mcp-thin-alignment.png
        eval/
            harness.py
            EVAL_REPORT.md
        golden_set/
        rag/
            fix_spec_rag.py
        fix_validator.py
        mcp_server.py
        langgraph_agent.py
        langgraph_agent_with_llm.py
        requirements.txt
        DEMO.md
        README.md

---

## Running Locally

Install the Python dependencies:

    pip install -r requirements.txt

Run the tests:

    python -m unittest discover -v

Run the canonical evaluation harness:

    python -m eval.harness

For the optional local LLM explanation prototype, see `DEMO.md`.

---

## Current Status

### Implemented

- deterministic FIX validation foundation
- PASS / FAIL / ESCALATE semantics
- MCP validation interface
- canonical executable golden-set harness
- explicit evaluation scope boundaries
- contextual Cancel/Replace escalation
- FIX delimiter normalization
- standard FIX Side handling
- reproducible runtime dependency declarations

### Scaffolded

- contextual FIX specification retrieval interface
- lightweight LangGraph/LLM workflow prototypes

### Planned

- venue-profile validation
- regulatory-profile validation
- authoritative order-state integration
- hybrid retrieval
- reranking
- measured RAG evaluation
- broader independent scenario coverage

---

**Building practical AI for real trading workflows — with executable evidence,
clear boundaries and honest evaluation.**