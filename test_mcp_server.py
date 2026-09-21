import unittest
from mcp_server import validate_new_order_single_tool, parse_execution_report_tool


class TestMcpVerdictPlumbing(unittest.TestCase):
    def test_nos_pass_retains_valid_and_adds_verdict(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1"
        )
        self.assertIsInstance(out, dict)
        self.assertTrue(out["valid"])
        self.assertEqual(out["verdict"], "PASS")
        self.assertIn("parsed", out)
        self.assertIn("errors", out)

    def test_nos_fail_retains_valid_and_adds_verdict(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|11=ORD2"
        )
        self.assertFalse(out["valid"])
        self.assertEqual(out["verdict"], "FAIL")

    def test_er_pass_retains_valid_and_adds_verdict(self):
        out = parse_execution_report_tool(
            "8=FIX.4.4|35=8|55=AAPL|39=2|32=1000|31=150.25"
        )
        self.assertTrue(out["valid"])
        self.assertEqual(out["verdict"], "PASS")


if __name__ == "__main__":
    unittest.main(verbosity=2)
