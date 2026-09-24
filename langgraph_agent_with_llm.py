import os
import requests

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

from fix_validator import (
    parse_execution_report,
    parse_fix,
    validate_new_order_single,
)


load_dotenv()


class AgentState(TypedDict):
    fix_msg: str
    errors: List[str]
    explanation: str

    # #004 Checkpoint 4:
    # Deterministic decision state produced before the LLM runs.
    valid: bool
    verdict: str
    decision_layer: str


def detect_node(state: AgentState):
    raw = state["fix_msg"]
    tags = parse_fix(raw)

    if tags.get("35") == "D":
        result = validate_new_order_single(raw)
    elif tags.get("35") == "8":
        result = parse_execution_report(raw)
    else:
        result = validate_new_order_single(raw)

    # #004 Checkpoint 4:
    # Preserve the deterministic decision as explicit graph state.
    # The downstream LLM receives a decision to explain; it does not
    # determine PASS/FAIL/ESCALATE itself.
    return {
        "valid": result.valid,
        "verdict": result.verdict,
        "decision_layer": result.decision_layer,
        "errors": result.errors,
    }


def explain_with_llm_node(state: AgentState):
    errors = state["errors"]
    verdict = state["verdict"]

    # #004 Checkpoint 4C:
    # Do not infer PASS from an empty error list. The deterministic
    # validator's frozen verdict remains authoritative.
    if not errors:
        return {
            "explanation": f"[{verdict}] FIX validation complete"
        }

    prompt = (
        f"Deterministic FIX verdict: {verdict}. "
        f"Explain to trader in 1 sentence: {errors}"
    )

    try:
        r = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3.2",
                "prompt": prompt,
                "stream": False,
            },
            timeout=60,
        )

        if r.status_code == 200:
            return {
                "explanation": (
                    f"[Ollama llama3.2] "
                    f"{r.json().get('response', '').strip()[:500]}"
                )
            }

    except Exception as e:
        print(f"Ollama failed: {e}")

    return {
        "explanation": (
            f"[{verdict}] [Fallback] {errors}"
        )
    }


def report_node(state: AgentState):
    # #004 Checkpoint 4C:
    # Presentation reports the frozen deterministic verdict rather
    # than hard-coding or reconstructing PASS/FAIL.
    verdict = state["verdict"]
    decision_layer = state["decision_layer"]

    print(
        f"[{verdict}] "
        f"{decision_layer or 'UNSPECIFIED'} -> "
        f"{state['errors']}"
    )
    print(f" -> {state['explanation']}")

    return {}


graph = StateGraph(AgentState)
graph.add_node("detect", detect_node)
graph.add_node("explain_with_llm", explain_with_llm_node)
graph.add_node("report", report_node)

graph.set_entry_point("detect")
graph.add_edge("detect", "explain_with_llm")
graph.add_edge("explain_with_llm", "report")
graph.add_edge("report", END)

app = graph.compile()


if __name__ == "__main__":
    test_fix = (
        "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|11=ORD123"
    )

    print(f"Testing: {test_fix}\n")

    app.invoke(
        {
            "fix_msg": test_fix,
            "errors": [],
            "explanation": "",
            "valid": False,
            "verdict": "",
            "decision_layer": "",
        }
    )