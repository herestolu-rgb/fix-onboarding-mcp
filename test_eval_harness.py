import unittest

from eval.harness import load_cases
from fix_validator import parse_fix


class TestEvalHarness(unittest.TestCase):
    def test_canonical_corpus_is_fully_accounted_for(self):
        cases = load_cases()

        self.assertEqual(len(cases), 70)

        msg_types = [
            parse_fix(case["input_raw"]).get("35")
            for case in cases
        ]

        self.assertEqual(msg_types.count("D"), 50)
        self.assertEqual(msg_types.count("G"), 20)
        self.assertEqual(len(msg_types), 70)

    def test_out_of_scope_cases_are_explicitly_classified(self):
        cases = load_cases()

        out_of_scope = [
            case
            for case in cases
            if case.get("evaluation_scope") == "OUT_OF_SCOPE"
        ]

        self.assertEqual(len(out_of_scope), 6)

        allowed_reasons = {
            "VENUE_FIRMUP_POLICY",
            "REGULATORY_LEI_POLICY",
        }

        for case in out_of_scope:
            self.assertIn("scope_reason", case)
            self.assertIn(case["scope_reason"], allowed_reasons)

        reasons = [
            case["scope_reason"]
            for case in out_of_scope
        ]

        self.assertEqual(reasons.count("VENUE_FIRMUP_POLICY"), 3)
        self.assertEqual(reasons.count("REGULATORY_LEI_POLICY"), 3)

    def test_venue_side_policy_cases_have_explicit_validation_context(self):
        cases = load_cases()

        venue_side_cases = [
            case
            for case in cases
            if case.get("expected_reason", "").startswith(
                "Invalid 54 Side=3 - only 1,2,5 allowed per VENUE_X"
            )
        ]

        self.assertEqual(len(venue_side_cases), 3)

        for case in venue_side_cases:
            self.assertNotEqual(
                case.get("evaluation_scope"),
                "OUT_OF_SCOPE",
            )
            self.assertEqual(
                case.get("validation_context"),
                {"venue_id": "VENUE_X"},
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)