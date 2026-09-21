# FIX Onboarding Validator - MCP Server

A prototype FIX onboarding validation system combining deterministic FIX
validation, an MCP interface, LangGraph workflow components, and an executable
golden-set evaluation harness.

## Current Implementation

### Deterministic FIX validation

The validator currently supports deterministic validation for selected FIX
message workflows, including:

- NewOrderSingle (`35=D`)
- ExecutionReport (`35=8`)
- Cancel/Replace (`35=G`) contextual validation
- FIX delimiters using SOH, pipe, or caret input
- explicit PASS / FAIL / ESCALATE verdict semantics

Venue-specific and regulatory policies are intentionally separated from the
generic validator where authoritative profile or contextual information is
required.

### MCP interface

`mcp_server.py` exposes validation functionality through the Model Context
Protocol while retaining the existing boolean `valid` result and adding an
explicit `verdict`.

### LangGraph

`langgraph_agent.py` and `langgraph_agent_with_llm.py` provide lightweight
LangGraph workflow prototypes.

The LLM-enhanced workflow currently attempts a local Ollama request using the
`llama3.2` model for error explanation. If Ollama is unavailable, it falls back
to a deterministic explanation.

This is a prototype workflow, not a production-ready multi-provider agent.

### Evaluation

The canonical corpus under `golden_set/` contains 70 cases.

Current executable harness result:

- Discovered: 70
- Evaluated: 61
- Out of scope: 9
- Unsupported: 0
- Matched: 61
- Mismatched: 0
- Unaccounted: 0

Run the harness with:

    python -m eval.harness

Run the unit tests with:

    python -m unittest discover -v

## RAG Status

`rag/fix_spec_rag.py` is currently a scaffold for a future contextual retrieval
layer.

The repository does not currently implement or measure:

- vector retrieval
- BM25 or reciprocal-rank fusion (RRF)
- Qdrant
- CrossEncoder reranking
- RAGAS faithfulness
- retrieval/context precision
- model confidence thresholds
- retrieval latency benchmarks

These remain planned architecture rather than current evaluation results.

The existing RAG architecture image is retained as a design artifact and should
not be interpreted as evidence that all depicted components are implemented.

![RAG design artifact](fix-onboarding-mcp_v0.2.0_RAG_EVAL.jpg)

## Planned Expansion

Future work can introduce an evidence-backed contextual layer for:

- FIX specification retrieval
- venue-specific onboarding profiles
- regulatory rule profiles
- hybrid retrieval and reranking
- context-grounded explanations
- measured RAG evaluation

Those capabilities should be added with executable tests and measured
evaluation rather than placeholder metrics.

## Project Structure

    fix-onboarding-mcp/
        eval/
        golden_set/
        rag/
        fix_validator.py
        mcp_server.py
        langgraph_agent.py
        langgraph_agent_with_llm.py
        requirements.txt
        README.md