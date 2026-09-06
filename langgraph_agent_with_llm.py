import os, requests
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from fix_validator import validate_new_order_single, parse_execution_report, parse_fix

load_dotenv()

class AgentState(TypedDict):
    fix_msg: str
    errors: List[str]
    explanation: str

def detect_node(state: AgentState):
    raw = state["fix_msg"]
    tags = parse_fix(raw)
    result = validate_new_order_single(raw) if tags.get("35")=="D" else parse_execution_report(raw) if tags.get("35")=="8" else validate_new_order_single(raw)
    return {"errors": result.errors}

def explain_with_llm_node(state: AgentState):
    errors = state["errors"]
    if not errors:
        return {"explanation": "[PASS] FIX valid"}
    prompt = f"Explain to trader in 1 sentence: {errors}"
    try:
        r = requests.post("http://localhost:11434/api/generate", json={"model": "llama3.2", "prompt": prompt, "stream": False}, timeout=60)
        if r.status_code == 200:
            return {"explanation": f"[Ollama llama3.2] {r.json().get('response','').strip()[:500]}"}
    except Exception as e:
        print(f"Ollama failed: {e}")
    return {"explanation": f"[Fallback] {errors} - Limit needs Price 44"}

def report_node(state: AgentState):
    print(f"[FAIL] D -> {state['errors']}")
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
    test_fix = "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|11=ORD123"
    print(f"Testing: {test_fix}\n")
    app.invoke({"fix_msg": test_fix, "errors": [], "explanation": ""})