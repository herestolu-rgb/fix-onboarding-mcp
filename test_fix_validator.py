import unittest
from datetime import datetime

from fix_validator import (
    ValidationResult,
    parse_execution_report,
    parse_fix,
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

    def test_invalid_side(self):
        r = validate_new_order_single(
            "8=FIX.4.4|35=D|55=AAPL|54=9|38=1000|40=1|11=ORD4"
        )

        self.assertFalse(r.valid)

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