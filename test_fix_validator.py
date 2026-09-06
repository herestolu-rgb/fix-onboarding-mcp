import unittest
from fix_validator import validate_new_order_single, parse_execution_report


class TestNewOrderSingle(unittest.TestCase):
    def test_valid_limit_order(self):
        r = validate_new_order_single("8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1")
        self.assertTrue(r.valid)
        self.assertEqual(r.parsed["price"], "150.25")

    def test_limit_order_missing_price(self):
        r = validate_new_order_single("8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|11=ORD2")
        self.assertFalse(r.valid)
        self.assertTrue(any("TAG_44_MISSING" in e for e in r.errors))

    def test_market_order_with_unexpected_price(self):
        r = validate_new_order_single("8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=1|44=150.25|11=ORD3")
        self.assertFalse(r.valid)
        self.assertTrue(any("TAG_44_UNEXPECTED" in e for e in r.errors))

    def test_invalid_side(self):
        r = validate_new_order_single("8=FIX.4.4|35=D|55=AAPL|54=9|38=1000|40=1|11=ORD4")
        self.assertFalse(r.valid)

    def test_missing_required_tags(self):
        r = validate_new_order_single("8=FIX.4.4|35=D|11=ORD5")
        self.assertFalse(r.valid)
        self.assertEqual(len(r.errors), 4)  # 55, 54, 38, 40 all missing


class TestExecutionReport(unittest.TestCase):
    def test_valid_fill(self):
        r = parse_execution_report("8=FIX.4.4|35=8|55=AAPL|39=2|32=1000|31=150.25")
        self.assertTrue(r.valid)
        self.assertEqual(r.parsed["status"], "Filled")

    def test_impossible_fill(self):
        r = parse_execution_report("8=FIX.4.4|35=8|55=AAPL|39=2")
        self.assertFalse(r.valid)
        self.assertTrue(any("IMPOSSIBLE_FILL" in e for e in r.errors))

    def test_valid_new_status(self):
        r = parse_execution_report("8=FIX.4.4|35=8|55=AAPL|39=0")
        self.assertTrue(r.valid)

    def test_wrong_msg_type(self):
        r = parse_execution_report("8=FIX.4.4|35=D|55=AAPL")
        self.assertFalse(r.valid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
