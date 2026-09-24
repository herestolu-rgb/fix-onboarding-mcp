import unittest

from mcp_server import (
    parse_execution_report_tool,
    validate_new_order_single_tool,
)


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

    # #004 Checkpoint 3A:
    # Structured decision provenance must survive the MCP boundary.
    def test_nos_protocol_decision_layer_is_exposed(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3"
        )

        self.assertTrue(out["valid"])
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(out["decision_layer"], "PROTOCOL")

    # #004 Checkpoint 3B:
    # TargetCompID is FIX message data. It must not silently acquire
    # authority to activate a venue policy at the MCP boundary.
    def test_comp_id_does_not_activate_policy_through_mcp(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|49=CLIENT|56=VENUE_X|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3"
        )

        self.assertTrue(out["valid"])
        self.assertEqual(out["verdict"], "PASS")
        self.assertEqual(out["decision_layer"], "PROTOCOL")

    # #004 Checkpoint 3B:
    # Explicit caller-supplied venue authority must cross the MCP boundary
    # and activate deterministic venue-policy validation.
    def test_explicit_venue_context_activates_policy_through_mcp(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3",
            venue_id="VENUE_X",
        )

        self.assertFalse(out["valid"])
        self.assertEqual(out["verdict"], "FAIL")
        self.assertEqual(out["decision_layer"], "POLICY")
        self.assertTrue(
            any(
                "VENUE_SIDE_POLICY" in error
                for error in out["errors"]
            )
        )

    # #004 Checkpoint 3B:
    # If explicit authority is requested but cannot be bound, the MCP
    # result must preserve the validator's abstention rather than guess.
    def test_unknown_explicit_venue_escalates_through_mcp(self):
        out = validate_new_order_single_tool(
            "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3",
            venue_id="VENUE_UNKNOWN",
        )

        self.assertFalse(out["valid"])
        self.assertEqual(out["verdict"], "ESCALATE")
        self.assertEqual(out["decision_layer"], "AUTHORITY")
        self.assertTrue(
            any(
                "AUTHORITY_UNAVAILABLE" in error
                for error in out["errors"]
            )
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)