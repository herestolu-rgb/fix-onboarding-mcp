# Local Prototype Demo

This demo exercises the current LangGraph + local Ollama prototype.

## Setup

Install the Python dependencies:

    pip install -r requirements.txt

The LLM-enhanced agent currently calls a local Ollama endpoint using the
`llama3.2` model.

If using the LLM explanation path, install Ollama separately and make that
model available locally.

## Run

    python langgraph_agent_with_llm.py

The current script uses its built-in sample FIX message.

It does not currently accept a `--fix-log` argument.

## Current Flow

The prototype:

1. parses the built-in FIX message
2. performs deterministic validation
3. freezes the deterministic verdict and decision provenance
4. attempts to obtain a short explanation from local Ollama
5. falls back to a deterministic explanation if the Ollama call fails
6. prints the frozen verdict and explanation

The LLM is used for explanation only. It does not own or mutate the
deterministic PASS / FAIL / ESCALATE verdict.

Executable tests deliberately exercise a contradictory LLM response to verify
that generated explanation text cannot change the deterministic validation
result.

The current demo does not demonstrate MCP tool invocation, sequence-gap
detection, hybrid RAG retrieval, or a multi-provider LLM factory.

## Planned Demo Expansion

Future versions may add:

- FIX log file input
- MCP-integrated workflow execution
- richer onboarding workflow orchestration
- provider abstraction for additional LLM backends
- contextual FIX/specification retrieval

These are planned capabilities and are not required to run the current
prototype.