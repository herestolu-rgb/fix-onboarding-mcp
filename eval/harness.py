import json
from datetime import datetime
from pathlib import Path

from fix_validator import (
    parse_fix,
    validate_cancel_replace,
    validate_new_order_single,
)


GOLDEN_ROOT = Path("golden_set")
GOLDEN_REFERENCE_TIME = datetime(2020, 1, 1, 0, 2, 0)


def load_cases():
    """Load the canonical golden evaluation corpus."""
    cases = []

    for path in sorted(GOLDEN_ROOT.glob("*/*.json")):
        with path.open(encoding="utf-8") as f:
            case = json.load(f)

        case["_source"] = str(path)
        cases.append(case)

    return cases


def evaluate():
    cases = load_cases()

    matched = 0
    mismatched = 0
    unsupported = 0
    out_of_scope = 0

    for case in cases:
        raw = case["input_raw"]
        expected = case["expected_verdict"]
        tags = parse_fix(raw)
        msg_type = tags.get("35")
        if case.get("evaluation_scope") == "OUT_OF_SCOPE":
            out_of_scope += 1
            print(
                f"{case['id']} "
                f"expected={expected} "
                f"status=OUT_OF_SCOPE "
                f"reason={case.get('scope_reason')}"
            )
            continue
        if msg_type == "D":
            result = validate_new_order_single(
                raw,
                reference_time=GOLDEN_REFERENCE_TIME,
            )
            actual = result.verdict

            if actual == expected:
                matched += 1
                status = "MATCH"
            else:
                mismatched += 1
                status = "MISMATCH"

            print(
                f"{case['id']} "
                f"expected={expected} actual={actual} status={status}"
            )

        elif msg_type == "G":
            result = validate_cancel_replace(raw)
            actual = result.verdict

            if actual == expected:
                matched += 1
                status = "MATCH"
            else:
                mismatched += 1
                status = "MISMATCH"

            print(
                f"{case['id']} "
                f"expected={expected} actual={actual} status={status}"
            )

        else:
            unsupported += 1
            print(
                f"{case['id']} "
                f"expected={expected} msg_type={msg_type} status=UNSUPPORTED"
            )

    evaluated = matched + mismatched
    discovered = len(cases)
    accounted = evaluated + unsupported + out_of_scope
    unaccounted = discovered - accounted

    print()
    print("Summary:")
    print(f"  Discovered:  {discovered}")
    print(f"  Evaluated:   {evaluated}")
    print(f"  OutOfScope:  {out_of_scope}")
    print(f"  Unsupported: {unsupported}")
    print(f"  Matched:     {matched}")
    print(f"  Mismatched:  {mismatched}")
    print(f"  Unaccounted: {unaccounted}")


if __name__ == "__main__":
    evaluate()