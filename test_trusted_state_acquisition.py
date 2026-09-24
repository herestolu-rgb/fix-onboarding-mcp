import unittest

from fix_validator import validate_cancel_replace


class TestTrustedStateAcquisition(unittest.TestCase):
    def test_matching_state_is_acquired_through_resolver(self):
        calls = []

        def resolve_order_state(orig_cl_ord_id):
            calls.append(orig_cl_ord_id)
            return {"55": "TEST.L"}

        result = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertEqual(calls, ["ORD1"])
        self.assertTrue(result.valid)
        self.assertEqual(result.verdict, "PASS")

    def test_caller_cannot_self_certify_authoritative_state(self):
        with self.assertRaises(TypeError):
            validate_cancel_replace(
                "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
                original_order={"55": "TEST.L"},
                original_order_source="AUTHORITATIVE",
            )

    def test_missing_resolver_escalates_with_no_resolver_reason(self):
        result = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L"
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.verdict, "ESCALATE")
        self.assertEqual(result.decision_layer, "AUTHORITY")
        self.assertTrue(
            any("NO_RESOLVER" in error for error in result.errors)
        )

    def test_resolver_not_found_escalates_with_authority_not_found_reason(self):
        calls = []

        def resolve_order_state(orig_cl_ord_id):
            calls.append(orig_cl_ord_id)
            return None

        result = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertEqual(calls, ["ORD1"])
        self.assertFalse(result.valid)
        self.assertEqual(result.verdict, "ESCALATE")
        self.assertEqual(result.decision_layer, "AUTHORITY")
        self.assertTrue(
            any("AUTHORITY_NOT_FOUND" in error for error in result.errors)
        )

    def test_resolver_failure_escalates_with_authority_unavailable_reason(self):
        calls = []

        def resolve_order_state(orig_cl_ord_id):
            calls.append(orig_cl_ord_id)
            raise RuntimeError("simulated authoritative state service failure")

        result = validate_cancel_replace(
            "8=FIX.4.2|35=G|11=ORD1_MOD|41=ORD1|55=TEST.L",
            resolve_order_state=resolve_order_state,
        )

        self.assertEqual(calls, ["ORD1"])
        self.assertFalse(result.valid)
        self.assertEqual(result.verdict, "ESCALATE")
        self.assertEqual(result.decision_layer, "AUTHORITY")
        self.assertTrue(
            any("AUTHORITY_UNAVAILABLE" in error for error in result.errors)
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)