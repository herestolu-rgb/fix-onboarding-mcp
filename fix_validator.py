"""
fix_validator.py
A small, genuinely-working FIX message parser and validator.
"""
from dataclasses import dataclass, field
from typing import Optional

TAG_NAMES = {
    "8": "BeginString", "35": "MsgType", "55": "Symbol", "54": "Side",
    "38": "OrderQty", "40": "OrdType", "44": "Price", "11": "ClOrdID",
    "39": "OrdStatus", "150": "ExecType", "32": "LastQty", "31": "LastPx",
}
SIDE_MAP = {"1": "Buy", "2": "Sell"}
ORD_TYPE_MAP = {"1": "Market", "2": "Limit"}
ORD_STATUS_MAP = {"0": "New", "1": "PartiallyFilled", "2": "Filled", "4": "Cancelled", "8": "Rejected"}

@dataclass
class ValidationResult:
    valid: bool
    msg_type: Optional[str] = None
    parsed: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    def __repr__(self):
        status = "PASS" if self.valid else "FAIL"
        return f"[{status}] {self.msg_type or '?'} -> {self.parsed if self.valid else self.errors}"

def parse_fix(raw: str) -> dict:
    tags = {}
    for pair in raw.split("|"):
        pair = pair.strip()
        if not pair or "=" not in pair: continue
        tag, value = pair.split("=", 1)
        tags[tag.strip()] = value.strip()
    return tags

def validate_new_order_single(raw: str) -> ValidationResult:
    tags = parse_fix(raw); errors = []
    if tags.get("35")!= "D":
        errors.append(f"MsgType is '{tags.get('35')}', expected 'D'")
        return ValidationResult(valid=False, msg_type=tags.get("35"), errors=errors)
    for tag in ["55","54","38","40"]:
        if tag not in tags:
            errors.append(f"TAG_{tag}_MISSING: {TAG_NAMES[tag]} is required for NewOrderSingle")
    side = tags.get("54")
    if side and side not in SIDE_MAP:
        errors.append(f"Side '{side}' is not recognised")
    ord_type = tags.get("40")
    if ord_type == "2" and "44" not in tags:
        errors.append("TAG_44_MISSING: Limit order (OrdType=2) requires Price (44)")
    if ord_type == "1" and "44" in tags:
        errors.append("TAG_44_UNEXPECTED: Market order (OrdType=1) should not include Price (44)")
    if errors:
        return ValidationResult(valid=False, msg_type="D", errors=errors)
    parsed = {"symbol": tags.get("55"), "side": SIDE_MAP.get(side, side), "qty": tags.get("38"), "ord_type": ORD_TYPE_MAP.get(ord_type, ord_type)}
    if "44" in tags: parsed["price"] = tags["44"]
    if "11" in tags: parsed["cl_ord_id"] = tags["11"]
    return ValidationResult(valid=True, msg_type="D", parsed=parsed)

def parse_execution_report(raw: str) -> ValidationResult:
    tags = parse_fix(raw); errors = []
    if tags.get("35")!= "8":
        errors.append(f"MsgType is '{tags.get('35')}', expected '8'")
        return ValidationResult(valid=False, msg_type=tags.get("35"), errors=errors)
    status = tags.get("39")
    if not status:
        errors.append("TAG_39_MISSING: OrdStatus is required")
    elif status not in ORD_STATUS_MAP:
        errors.append(f"OrdStatus '{status}' not recognised")
    elif status in ("1","2"):
        if "32" not in tags or "31" not in tags:
            errors.append(f"IMPOSSIBLE_FILL: OrdStatus={status} ({ORD_STATUS_MAP[status]}) but LastQty (32) and/or LastPx (31) missing")
    if errors:
        return ValidationResult(valid=False, msg_type="8", errors=errors)
    parsed = {"status": ORD_STATUS_MAP.get(status, status), "symbol": tags.get("55")}
    if "32" in tags: parsed["last_qty"] = tags["32"]
    if "31" in tags: parsed["last_px"] = tags["31"]
    return ValidationResult(valid=True, msg_type="8", parsed=parsed)