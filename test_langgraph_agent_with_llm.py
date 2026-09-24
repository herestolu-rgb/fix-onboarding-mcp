import unittest
from unittest.mock import Mock, patch

from langgraph_agent_with_llm import (
    app,
    detect_node,
    explain_with_llm_node,
    report_node,
)


class TestDeterministicDecisionFreezePoint(unittest.TestCase):
    def test_detect_node_preserves_protocol_pass_decision(self):
        state = {
            "fix_msg": (
                "8=FIX.4.4|35=D|55=AAPL|54=3|38=1000|40=1|11=ORD_SIDE3"
            ),
            "errors": [],
            "explanation": "",
        }

        out = detect_node(state)

        self.assertEqual(out["verdict"], "PASS")
        self.assertTrue(out["valid"])
        self.assertEqual(out["decision_layer"], "PROTOCOL")
        self.assertEqual(out["errors"], [])

    def test_detect_node_preserves_protocol_fail_decision(self):
        state = {
            "fix_msg": (
                "8=FIX.4.4|35=D|55=AAPL|54=Z|38=1000|40=1|11=ORD_BAD_SIDE"
            ),
            "errors": [],
            "explanation": "",
        }

        out = detect_node(state)

        self.assertEqual(out["verdict"], "FAIL")
        self.assertFalse(out["valid"])
        self.assertEqual(out["decision_layer"], "PROTOCOL")
        self.assertTrue(
            any("not recognised" in error for error in out["errors"])
        )

    @patch("langgraph_agent_with_llm.requests.post")
    def test_llm_cannot_mutate_deterministic_fail_verdict(self, mock_post):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {
            "response": (
                "This FIX order is valid and should be accepted."
            )
        }
        mock_post.return_value = response

        final_state = app.invoke(
            {
                "fix_msg": (
                    "8=FIX.4.4|35=D|55=AAPL|54=Z|38=1000|40=1|11=ORD_BAD_SIDE"
                ),
                "errors": [],
                "explanation": "",
                "valid": False,
                "verdict": "",
                "decision_layer": "",
            }
        )

        self.assertFalse(final_state["valid"])
        self.assertEqual(final_state["verdict"], "FAIL")
        self.assertEqual(
            final_state["decision_layer"],
            "PROTOCOL",
        )

        self.assertIn(
            "valid and should be accepted",
            final_state["explanation"],
        )

    # #004 Checkpoint 4C:
    # A no-error explanation must use the frozen deterministic verdict,
    # rather than infer PASS merely because the error list is empty.
    def test_no_error_explanation_uses_frozen_verdict(self):
        state = {
            "fix_msg": "irrelevant-for-this-node",
            "errors": [],
            "explanation": "",
            "valid": False,
            "verdict": "ESCALATE",
            "decision_layer": "AUTHORITY",
        }

        out = explain_with_llm_node(state)

        self.assertIn("[ESCALATE]", out["explanation"])
        self.assertNotIn("[PASS]", out["explanation"])

    # #004 Checkpoint 4C:
    # Reporting must present the frozen verdict, not hard-code FAIL.
    @patch("builtins.print")
    def test_report_node_uses_frozen_verdict(self, mock_print):
        state = {
            "fix_msg": (
                "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=1|11=ORD_PASS"
            ),
            "errors": [],
            "explanation": "[PASS] FIX valid",
            "valid": True,
            "verdict": "PASS",
            "decision_layer": "PROTOCOL",
        }

        report_node(state)

        printed = " ".join(
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        )

        self.assertIn("[PASS]", printed)
        self.assertNotIn("[FAIL]", printed)


if __name__ == "__main__":
    unittest.main(verbosity=2)