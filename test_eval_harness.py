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


if __name__ == "__main__":
    unittest.main(verbosity=2)