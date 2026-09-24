"""
fix_validator.py
A small, genuinely-working FIX message parser and validator.
"""

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional


TAG_NAMES = {
    "8": "BeginString",
    "35": "MsgType",
    "55": "Symbol",
    "54": "Side",
    "38": "OrderQty",
    "40": "OrdType",
    "44": "Price",
    "11": "ClOrdID",
    "41": "OrigClOrdID",
    "39": "OrdStatus",
    "150": "ExecType",
    "32": "LastQty",
    "31": "LastPx",
}

SIDE_MAP = {
    "1": "Buy",
    "2": "Sell",
    "3": "Buy Minus",
    "4": "Sell Plus",
    "5": "Sell Short",
    "6": "Sell Short Exempt",
    "7": "Undisclosed",
    "8": "Cross",
    "9": "Cross Short",
    "A": "Cross Short Exempt",
    "B": "As Defined",
    "C": "Opposite",
    "D": "Subscribe",
    "E": "Redeem",
    "F": "Lend",
    "G": "Borrow",
    "H": "Sell Undisclosed",
}

ORD_TYPE_MAP = {
    "1": "Market",
    "2": "Limit",
}

ORD_STATUS_MAP = {
    "0": "New",
    "1": "PartiallyFilled",
    "2": "Filled",
    "4": "Cancelled",
    "8": "Rejected",
}


# #004 structured venue-policy data.
#
# This is deliberately small for the first implementation slice.
# The FIX protocol remains responsible for determining whether a Side
# value is recognised. Venue policy answers the separate question:
# "Does this explicitly selected venue allow that otherwise-valid Side?"
VENUE_POLICIES = {
    "VENUE_X": {
        "allowed_sides": {"1", "2", "5"},
    },
}


@dataclass(frozen=True)
class ValidationContext:
    """Explicit caller-supplied context for contextual validation.

    Message fields such as SenderCompID (49) and TargetCompID (56) are
    FIX data. They do not implicitly grant authority to apply a venue
    policy. Venue policy is activated only through explicit context.
    """

    venue_id: Optional[str] = None


@dataclass
class ValidationResult:
    valid: bool
    msg_type: Optional[str] = None
    parsed: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)
    verdict: Optional[str] = None

    def __post_init__(self):
        # Single source of truth: verdict. If omitted, derive PASS/FAIL from valid
        # (current call sites). Then valid is always (verdict == "PASS"), so
        # FAIL and ESCALATE both have valid == False.
        if self.verdict is None:
            self.verdict = "PASS" if self.valid else "FAIL"

        if self.verdict not in ("PASS", "FAIL", "ESCALATE"):
            raise ValueError(
                f"verdict must be PASS, FAIL, or ESCALATE, got {self.verdict!r}"
            )

        self.valid = self.verdict == "PASS"

    def __repr__(self):
        return (
            f"[{self.verdict}] {self.msg_type or '?'} -> "
            f"{self.parsed if self.valid else self.errors}"
        )


def parse_fix(raw: str) -> dict:
    """Split a FIX-style tag string into a dict.

    SOH (\\x01) is the wire delimiter. '|' and '^' are accepted as
    human-readable stand-ins when SOH is absent. Pair parsing is unchanged.
    """
    if "\x01" in raw:
        sep = "\x01"
    elif "|" in raw:
        sep = "|"
    elif "^" in raw:
        sep = "^"
    else:
        sep = "|"

    tags = {}

    for pair in raw.split(sep):
        pair = pair.strip()

        if not pair or "=" not in pair:
            continue

        tag, value = pair.split("=", 1)
        tags[tag.strip()] = value.strip()

    return tags


def validate_new_order_single(
    raw: str,
    reference_time: Optional[datetime] = None,
    context: Optional[ValidationContext] = None,
) -> ValidationResult:
    tags = parse_fix(raw)
    errors = []

    if tags.get("35") != "D":
        errors.append(
            f"MsgType is '{tags.get('35')}', expected 'D'"
        )
        return ValidationResult(
            valid=False,
            msg_type=tags.get("35"),
            errors=errors,
        )

    # Required NewOrderSingle fields.
    for tag in ["11", "55", "54", "38", "40"]:
        if tag not in tags:
            errors.append(
                f"TAG_{tag}_MISSING: "
                f"{TAG_NAMES[tag]} is required for NewOrderSingle"
            )

    # OrderQty must be numeric and greater than zero when present.
    qty = tags.get("38")

    if qty is not None:
        try:
            if Decimal(qty) <= 0:
                errors.append(
                    "TAG_38_INVALID: OrderQty must be greater than 0"
                )
        except InvalidOperation:
            errors.append(
                "TAG_38_INVALID: OrderQty must be numeric"
            )

    # SendingTime is optional in this lightweight validator.
    # If a deterministic reference time is supplied, validate its age.
    sending_time = tags.get("52")

    if sending_time is not None and reference_time is not None:
        try:
            parsed_sending_time = datetime.strptime(
                sending_time,
                "%Y%m%d-%H:%M:%S",
            )

            age_seconds = (
                reference_time - parsed_sending_time
            ).total_seconds()

            if age_seconds > 60:
                errors.append(
                    "TAG_52_STALE: SendingTime is more than 60 seconds old"
                )

        except ValueError:
            errors.append(
                "TAG_52_INVALID: SendingTime must use YYYYMMDD-HH:MM:SS"
            )

    side = tags.get("54")

    # Protocol-layer validation.
    #
    # A recognised Side value is valid FIX regardless of whether a
    # particular venue subsequently chooses to permit it.
    if side and side not in SIDE_MAP:
        errors.append(
            f"Side '{side}' is not recognised"
        )

    ord_type = tags.get("40")

    if ord_type == "2" and "44" not in tags:
        errors.append(
            "TAG_44_MISSING: Limit order (OrdType=2) requires Price (44)"
        )

    if ord_type == "1" and "44" in tags:
        errors.append(
            "TAG_44_UNEXPECTED: Market order (OrdType=1) "
            "should not include Price (44)"
        )

    # Protocol failures take precedence. Do not apply contextual policy
    # to a message that is already invalid at the FIX protocol layer.
    if errors:
        return ValidationResult(
            valid=False,
            msg_type="D",
            errors=errors,
        )

    # #004 contextual-policy validation.
    #
    # Policy authority is activated only by explicit caller-supplied
    # ValidationContext. We deliberately do NOT infer venue authority
    # from FIX fields such as TargetCompID (56).
    if context is not None and context.venue_id is not None:
        venue_policy = VENUE_POLICIES.get(context.venue_id)

        # #004 GREEN 2:
        # Explicit policy validation was requested, but the requested
        # authority cannot be bound. Abstain rather than guessing.
        if venue_policy is None:
            return ValidationResult(
                valid=False,
                msg_type="D",
                verdict="ESCALATE",
                errors=[
                    "AUTHORITY_UNAVAILABLE: "
                    f"No authoritative venue policy is available for "
                    f"'{context.venue_id}'"
                ],
            )

        allowed_sides = venue_policy["allowed_sides"]

        if side not in allowed_sides:
            return ValidationResult(
                valid=False,
                msg_type="D",
                errors=[
                    "VENUE_SIDE_POLICY: "
                    f"Side '{side}' ({SIDE_MAP.get(side, side)}) "
                    f"is not permitted by venue "
                    f"'{context.venue_id}'"
                ],
            )

    parsed = {
        "symbol": tags.get("55"),
        "side": SIDE_MAP.get(side, side),
        "qty": tags.get("38"),
        "ord_type": ORD_TYPE_MAP.get(ord_type, ord_type),
    }

    if "44" in tags:
        parsed["price"] = tags["44"]

    if "11" in tags:
        parsed["cl_ord_id"] = tags["11"]

    return ValidationResult(
        valid=True,
        msg_type="D",
        parsed=parsed,
    )


def validate_cancel_replace(
    raw: str,
    original_order: Optional[dict] = None,
) -> ValidationResult:
    """Validate an Order Cancel/Replace Request (35=G).

    Some replacement checks require authoritative state from the original
    order. If that context is unavailable, return ESCALATE rather than
    guessing PASS or FAIL.
    """
    tags = parse_fix(raw)
    errors = []

    if tags.get("35") != "G":
        return ValidationResult(
            valid=False,
            msg_type=tags.get("35"),
            errors=[
                f"MsgType is '{tags.get('35')}', expected 'G'"
            ],
        )

    # Minimal deterministic fields needed for the contextual check.
    for tag in ["11", "41", "55"]:
        if tag not in tags:
            errors.append(
                f"TAG_{tag}_MISSING: "
                f"{TAG_NAMES[tag]} is required for Order Cancel/Replace"
            )

    if errors:
        return ValidationResult(
            valid=False,
            msg_type="G",
            errors=errors,
        )

    # The replacement references an original order via OrigClOrdID (41).
    # Without authoritative original-order state, we cannot determine
    # whether fields such as Symbol conflict with that order.
    if original_order is None:
        return ValidationResult(
            valid=False,
            msg_type="G",
            verdict="ESCALATE",
            errors=[
                "CONTEXT_REQUIRED: Original order state is required "
                "to validate Order Cancel/Replace"
            ],
        )

    original_symbol = original_order.get("55")
    replacement_symbol = tags.get("55")

    if original_symbol is None:
        return ValidationResult(
            valid=False,
            msg_type="G",
            verdict="ESCALATE",
            errors=[
                "CONTEXT_REQUIRED: Original order Symbol (55) "
                "is unavailable"
            ],
        )

    if replacement_symbol != original_symbol:
        return ValidationResult(
            valid=False,
            msg_type="G",
            errors=[
                "TAG_55_MISMATCH: Replacement Symbol does not match "
                "original order Symbol"
            ],
        )

    return ValidationResult(
        valid=True,
        msg_type="G",
        parsed={
            "cl_ord_id": tags.get("11"),
            "orig_cl_ord_id": tags.get("41"),
            "symbol": replacement_symbol,
        },
    )


def parse_execution_report(raw: str) -> ValidationResult:
    tags = parse_fix(raw)
    errors = []

    if tags.get("35") != "8":
        errors.append(
            f"MsgType is '{tags.get('35')}', expected '8'"
        )
        return ValidationResult(
            valid=False,
            msg_type=tags.get("35"),
            errors=errors,
        )

    status = tags.get("39")

    if not status:
        errors.append(
            "TAG_39_MISSING: OrdStatus is required"
        )

    elif status not in ORD_STATUS_MAP:
        errors.append(
            f"OrdStatus '{status}' not recognised"
        )

    elif status in ("1", "2"):
        if "32" not in tags or "31" not in tags:
            errors.append(
                f"IMPOSSIBLE_FILL: OrdStatus={status} "
                f"({ORD_STATUS_MAP[status]}) but LastQty (32) "
                f"and/or LastPx (31) missing"
            )

    if errors:
        return ValidationResult(
            valid=False,
            msg_type="8",
            errors=errors,
        )

    parsed = {
        "status": ORD_STATUS_MAP.get(status, status),
        "symbol": tags.get("55"),
    }

    if "32" in tags:
        parsed["last_qty"] = tags["32"]

    if "31" in tags:
        parsed["last_px"] = tags["31"]

    return ValidationResult(
        valid=True,
        msg_type="8",
        parsed=parsed,
    )