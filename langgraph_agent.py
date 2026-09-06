"""
Real LangGraph agent — 3 nodes, conditional routing, uses your real validator
"""
from typing import TypedDict
from langgraph.graph import StateGraph, END
from fix_validator import parse_fix, validate_new_order_single, parse_execution_report

class AgentState(TypedDict):
    message: str
    validation_result: object
    report: str

def detect_and_validate(state: AgentState):
    msg = state["message"]
    tags = parse_fix(msg)
    msg_type = tags.get("35", "")
    if msg_type == "D":
        result = validate_new_order_single(msg)
    elif msg_type == "8":
        result = parse_execution_report(msg)
    else:
        from fix_validator import ValidationResult
        result = ValidationResult(valid=False, msg_type=msg_type, errors=[f"Unknown MsgType {msg_type}"])
    return {"validation_result": result}

def report_pass(state: AgentState):
    r = state["validation_result"]
    return {"report": f"✅ {r}"}

def report_fail(state: AgentState):
    r = state["validation_result"]
    return {"report": f"❌ {r}"}

def should_pass(state: AgentState):
    r = state["validation_result"]
    return "pass" if r.valid else "fail"

graph = StateGraph(AgentState)
graph.add_node("detect_and_validate", detect_and_validate)
graph.add_node("report_pass", report_pass)
graph.add_node("report_fail", report_fail)
graph.set_entry_point("detect_and_validate")
graph.add_conditional_edges("detect_and_validate", should_pass, {"pass": "report_pass", "fail": "report_fail"})
graph.add_edge("report_pass", END)
graph.add_edge("report_fail", END)
app = graph.compile()

if __name__ == "__main__":
    test_cases = [
        "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|11=ORD123",
        "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD123",
        "8=FIX.4.4|35=D|55=AAPL|54=9|38=1000|40=1|11=ORD124",
        "8=FIX.4.4|35=8|55=AAPL|39=2|32=1000|31=150.25",
        "8=FIX.4.4|35=8|55=AAPL|39=2",
    ]
    print("="*70)
    print("REAL LangGraph agent — actual graph execution")
    print("="*70)
    for msg in test_cases:
        out = app.invoke({"message": msg})
        print(out["report"])