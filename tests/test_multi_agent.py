import json
from pathlib import Path
import unittest

from orchestration.delegation import build_delegation_plan, specialists_for_question
from orchestration.router import deterministic_route

ROOT = Path(__file__).resolve().parents[1]


class SpecialistPlanningTests(unittest.TestCase):
    def test_single_domain_selects_one_specialist(self):
        self.assertEqual(
            specialists_for_question("Which products are below safety stock?"),
            ("inventory_specialist",),
        )

    def test_cross_domain_selects_multiple_specialists(self):
        question = "Which suppliers contribute to inventory shortages and overdue fulfilment orders?"
        self.assertEqual(deterministic_route(question).route, "CROSS_DOMAIN")
        self.assertEqual(
            specialists_for_question(question),
            ("inventory_specialist", "supplier_specialist", "fulfilment_specialist"),
        )

    def test_plan_rejects_requests_above_call_bound(self):
        with self.assertRaises(ValueError):
            build_delegation_plan(
                "Which suppliers contribute to inventory shortages and overdue fulfilment orders?",
                max_specialist_calls=2,
            )

    def test_invalid_call_bound_rejected(self):
        with self.assertRaises(ValueError):
            build_delegation_plan("inventory", max_specialist_calls=0)

    def test_eval_fixture_is_consistent(self):
        cases = json.loads((ROOT / "evals" / "multi_agent_eval_cases.json").read_text())
        for case in cases["cases"]:
            self.assertEqual(deterministic_route(case["question"]).route, case["expected_route"], case["id"])
            self.assertEqual(list(specialists_for_question(case["question"])), case["expected_specialists"], case["id"])


if __name__ == "__main__":
    unittest.main()
