import unittest
from datetime import datetime

from fix_validator import (
    ValidationContext,
    ValidationResult,
    parse_execution_report,
    parse_fix,
    validate_cancel_replace,
    validate_new_order_single,
)


class TestParseFixDelimiters(unittest.TestCase):
    def test_pipe_caret_soh_equivalent(self):
        pipe = "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1"
        caret = "8=FIX.4.4^35=D^55=AAPL^54=1^38=1000^40=2^44=150.25^11=ORD1"
        soh = "8=FIX.4.4\x0135=D\x0155=AAPL\x0154=1\x0138=1000\x0140=2\x0144=150.25\x0111=ORD1"

        expected = parse_fix(pipe)

        self.assertEqual(parse_fix(caret), expected)
        self.assertEqual(parse_fix(soh), expected)


class TestValidationResultVerdict(unittest.TestCase):
    def test_unsupported_verdict_rejected(self):
        with self.assertRaises(ValueError):
            ValidationResult(
                valid=False,
                verdict="BANANA",
            )


class TestNewOrderSingle(unittest.TestCase):
    def test_valid_limit_order(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1"
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.parsed["side"], "Buy")
        self.assertEqual(r.parsed["price"], "150.25")

    def test_limit_order_missing_price(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=2|38=500|40=2|11=ORD2"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_44_MISSING" in error for error in r.errors)
        )

    def test_market_order_with_unexpected_price(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=1|44=150.25|11=ORD3"
        )

        self.assertFalse(r.valid)

    def test_standard_side_code_is_valid(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=9|38=1000|40=1|11=ORD4"
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.parsed["side"], "Cross Short")

    def test_unrecognised_side_code_is_invalid(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=Z|38=1000|40=1|11=ORD4"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")

    # #004 baseline protection:
    # Side=3 is valid at the generic FIX protocol layer.
    def test_side_3_is_protocol_valid_without_venue_context(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3"
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.parsed["side"], "Buy Minus")

        # #004 Checkpoint 2:
        # The result must identify the layer that made the decision.
        self.assertEqual(r.decision_layer, "PROTOCOL")

    # #004 authority boundary:
    # CompID is message data and must not silently activate venue policy.
    def test_comp_id_does_not_imply_venue_policy(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|49=CLIENT|56=VENUE_X|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3"
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.parsed["side"], "Buy Minus")

    # #004 contextual-policy requirement:
    # Explicit caller-supplied venue context activates venue policy.
    def test_explicit_venue_context_rejects_side_3(self):
        context = ValidationContext(
            venue_id="VENUE_X",
        )

        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3",
            context=context,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("VENUE_SIDE_POLICY" in error for error in r.errors)
        )

        # #004 Checkpoint 2:
        self.assertEqual(r.decision_layer, "POLICY")

    # #004 contextual-policy requirement:
    # A known venue policy must also allow values explicitly permitted by it.
    def test_explicit_venue_context_allows_permitted_side(self):
        context = ValidationContext(
            venue_id="VENUE_X",
        )

        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=1|11=ORD_SIDE1",
            context=context,
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.parsed["side"], "Buy")

        # #004 Checkpoint 2:
        # Protocol validation passed, but explicit venue policy made the
        # final contextual decision.
        self.assertEqual(r.decision_layer, "POLICY")

    # #004 authority boundary:
    # If explicit contextual validation is requested but the authority
    # cannot be bound, the validator must abstain rather than guess.
    def test_unknown_explicit_venue_context_escalates(self):
        context = ValidationContext(
            venue_id="VENUE_UNKNOWN",
        )

        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3",
            context=context,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "ESCALATE")
        self.assertTrue(
            any("AUTHORITY_UNAVAILABLE" in error for error in r.errors)
        )

        # #004 Checkpoint 2:
        self.assertEqual(r.decision_layer, "AUTHORITY")

    # #004 protocol-first requirement:
    # Protocol-invalid data must fail before contextual policy is considered.
    def test_protocol_failure_precedes_contextual_policy(self):
        context = ValidationContext(
            venue_id="VENUE_UNKNOWN",
        )

        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=Z|38=1000|40=1|11=ORD_BAD_SIDE",
            context=context,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("not recognised" in error for error in r.errors)
        )
        self.assertFalse(
            any("AUTHORITY_UNAVAILABLE" in error for error in r.errors)
        )

    def test_missing_required_tags(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|11=ORD5"
        )

        self.assertFalse(r.valid)
        self.assertEqual(
            len(r.errors),
            4,
        )  # 55, 54, 38, 40 all missing

    def test_missing_cl_ord_id(self):
        r = validate_new_order_single(
            "8=FIX.4.2|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_11_MISSING" in error for error in r.errors)
        )

    def test_zero_order_qty(self):
        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=0|40=2|44=150.25"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_38_INVALID" in error for error in r.errors)
        )

    def test_negative_order_qty(self):
        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=-10|40=2|44=150.25"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_38_INVALID" in error for error in r.errors)
        )

    def test_non_numeric_order_qty(self):
        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=ABC|40=2|44=150.25"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_38_INVALID" in error for error in r.errors)
        )

    def test_stale_sending_time(self):
        reference_time = datetime(
            2020,
            1,
            1,
            0,
            2,
            0,
        )

        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=1000|40=2|44=150.25|52=20200101-00:00:00",
            reference_time=reference_time,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_52_STALE" in error for error in r.errors)
        )

    def test_fresh_sending_time(self):
        reference_time = datetime(
            2020,
            1,
            1,
            0,
            0,
            30,
        )

        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=1000|40=2|44=150.25|52=20200101-00:00:00",
            reference_time=reference_time,
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")

    def test_invalid_sending_time(self):
        reference_time = datetime(
            2020,
            1,
            1,
            0,
            2,
            0,
        )

        r = validate_new_order_single(
            "8=FIX.4.2|35=D|11=ORD1|55=AAPL|54=1|38=1000|40=2|44=150.25|52=NOT-A-TIME",
            reference_time=reference_time,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertTrue(
            any("TAG_52_INVALID" in error for error in r.errors)
        )


class TestCancelReplace(unittest.TestCase):
    def test_missing_order_state_resolver_escalates(self):
        r = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=DIFF.L"
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "ESCALATE")
        self.assertEqual(r.decision_layer, "AUTHORITY")
        self.assertTrue(
            any("NO_RESOLVER" in error for error in r.errors)
        )

    def test_resolver_matching_original_symbol_passes(self):
        def resolve_order_state(orig_cl_ord_id):
            self.assertEqual(orig_cl_ord_id, "ORD1")
            return {"55": "TEST.L"}

        r = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.verdict, "PASS")
        self.assertEqual(r.decision_layer, "POLICY")

    def test_resolver_symbol_mismatch_fails(self):
        def resolve_order_state(orig_cl_ord_id):
            self.assertEqual(orig_cl_ord_id, "ORD1")
            return {"55": "TEST.L"}

        r = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=DIFF.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertEqual(r.decision_layer, "POLICY")
        self.assertTrue(
            any("TAG_55_MISMATCH" in error for error in r.errors)
        )

    def test_resolver_not_found_escalates(self):
        def resolve_order_state(orig_cl_ord_id):
            self.assertEqual(orig_cl_ord_id, "ORD1")
            return None

        r = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "ESCALATE")
        self.assertEqual(r.decision_layer, "AUTHORITY")
        self.assertTrue(
            any("AUTHORITY_NOT_FOUND" in error for error in r.errors)
        )

    def test_missing_orig_cl_ord_id_fails_before_resolver(self):
        calls = []

        def resolve_order_state(orig_cl_ord_id):
            calls.append(orig_cl_ord_id)
            return {"55": "TEST.L"}

        r = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertEqual(r.decision_layer, "PROTOCOL")
        self.assertEqual(calls, [])
        self.assertTrue(
            any("TAG_41_MISSING" in error for error in r.errors)
        )

    def test_wrong_msg_type_fails_before_resolver(self):
        calls = []

        def resolve_order_state(orig_cl_ord_id):
            calls.append(orig_cl_ord_id)
            return {"55": "TEST.L"}

        r = validate_cancel_replace(
            "8=FIX.4.2|35=D|11=ORD1|41=OLD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertFalse(r.valid)
        self.assertEqual(r.verdict, "FAIL")
        self.assertEqual(r.decision_layer, "PROTOCOL")
        self.assertEqual(calls, [])


class TestExecutionReport(unittest.TestCase):
    def test_valid_fill(self):
        r = parse_execution_report(
            "8=FIX.4.4|35=8|55=AAPL|39=2|32=1000|31=150.25"
        )

        self.assertTrue(r.valid)
        self.assertEqual(r.parsed["status"], "Filled")

    def test_valid_new_status(self):
        r = parse_execution_report(
            "8=FIX.4.4|35=8|55=AAPL|39=0"
        )

        self.assertTrue(r.valid)

    def test_impossible_fill(self):
        r = parse_execution_report(
            "8=FIX.4.4|35=8|55=AAPL|39=2"
        )

        self.assertFalse(r.valid)
        self.assertTrue(
            any("IMPOSSIBLE_FILL" in error for error in r.errors)
        )

    def test_wrong_msg_type(self):
        r = parse_execution_report(
            "8=FIX.4.4|35=D|55=AAPL|39=0"
        )

        self.assertFalse(r.valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
