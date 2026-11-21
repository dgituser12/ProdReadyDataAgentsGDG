import unittest
from types import SimpleNamespace

from orchestration.router import (
    ROUTES, deterministic_route, decision1_route, route_question
)
from orchestration.tracks import run_track_a
from orchestration.policy import (
    ROUTE_TOOLS, tools_for_route, invoke_routed_tool, prepare_request,
    build_grounded_answer_context
)


class FakeDecisions:
    def __init__(self, choice="INVENTORY_RISK", confidence=0.95, error=None):
        self.choice = choice
        self.confidence = confidence
        self.error = error
        self.calls = []
        self.decisions = self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(answers={
            "route": SimpleNamespace(choice=self.choice, confidence=self.confidence)
        })


class RoutingTests(unittest.TestCase):
    def test_local_routing_routes_supported_domains(self):
        self.assertEqual(deterministic_route("Which products are below safety stock?").route,
                         "INVENTORY_RISK")
        self.assertEqual(deterministic_route("Compare supplier on-time delivery rate").route,
                         "SUPPLIER_RISK")
        self.assertEqual(deterministic_route("Which orders are overdue?").route,
                         "FULFILMENT_DELAY")

    def test_local_router_routes_explicit_cross_domain_questions(self):
        result = deterministic_route("Compare supplier inventory and fulfilment delays")
        self.assertEqual(result.route, "CROSS_DOMAIN")

    def test_decision_api_request_contract_and_route_validation(self):
        fake = FakeDecisions()
        result = decision1_route("Which products are low on stock?", fake)
        self.assertEqual(result.route, "INVENTORY_RISK")
        self.assertEqual(result.source, "gemini_decision_1")
        self.assertEqual(fake.calls[0]["model"], "gemini-decision-1")
        self.assertEqual(fake.calls[0]["questions"]["route"]["type"], "choice")
        self.assertEqual(set(fake.calls[0]["questions"]["route"]["criteria"]), set(ROUTES))

    def test_low_confidence_falls_back_to_local(self):
        result = decision1_route(
            "Which orders are overdue?",
            FakeDecisions(choice="SUPPLIER_RISK", confidence=0.40),
        )
        self.assertEqual(result.route, "FULFILMENT_DELAY")
        self.assertEqual(result.source, "local_fallback_low_confidence")

    def test_api_error_falls_back_to_local(self):
        result = decision1_route(
            "Which products are below safety stock?",
            FakeDecisions(error=TimeoutError()),
        )
        self.assertEqual(result.route, "INVENTORY_RISK")
        self.assertEqual(result.source, "local_fallback_error")

    def test_feature_flag_defaults_to_local(self):
        result = route_question("Which products are below safety stock?", use_decision_model=False)
        self.assertEqual(result.source, "local_rules")


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        self.functions = {
            name: (lambda n=name, **kwargs: self.calls.append((n, kwargs)) or {"ok": True})
            for name in {
                "get_inventory_risk", "get_inventory_summary",
                "get_supplier_performance", "get_fulfillment_exposure",
                "get_fulfillment_summary",
            }
        }

    def test_route_tool_allowlists(self):
        self.assertEqual(set(tools_for_route("SUPPLIER_RISK", self.functions)),
                         {"get_supplier_performance"})
        self.assertEqual(tools_for_route("UNCERTAIN", self.functions), {})

    def test_forbidden_tool_rejected(self):
        with self.assertRaises(PermissionError):
            invoke_routed_tool("SUPPLIER_RISK", "get_inventory_risk", {}, self.functions)
        self.assertEqual(self.calls, [])

    def test_allowed_tool_invoked(self):
        result = invoke_routed_tool("INVENTORY_RISK", "get_inventory_risk",
                                    {"inventory_status": "CRITICAL"}, self.functions)
        self.assertTrue(result["ok"])
        self.assertEqual(self.calls[0][0], "get_inventory_risk")

    def test_uncertain_request_exposes_no_tools(self):
        prepared = prepare_request("Can you look at this?", self.functions,
                                   use_decision_model=False)
        self.assertEqual(prepared["decision"]["route"], "GENERAL_QUESTION")
        # Explicitly ambiguous cross-domain request.
        prepared = prepare_request("Compare supplier inventory stock and order delay",
                                   self.functions, use_decision_model=False)
        self.assertFalse(prepared["needs_clarification"])
        self.assertEqual(prepared["decision"]["route"], "CROSS_DOMAIN")
        self.assertEqual(prepared["tools"], {})

    def test_answer_context_contains_canonical_scope(self):
        ctx = build_grounded_answer_context({"route": "INVENTORY_RISK"}, {"rows": []})
        self.assertEqual(ctx["currency"], "GBP")
        self.assertEqual(ctx["warehouse_scope"], "WH-ESSEX-01")
        self.assertIn("semantic_catalogue/metrics.json", ctx["metric_source"])


class TrackIntegrationTests(unittest.TestCase):
    def test_track_a_passes_cross_domain_route_to_managed_agent(self):
        captured = {}

        def managed(**kwargs):
            captured.update(kwargs)
            return {"summary": "evidence returned"}

        result = run_track_a(
            "Which suppliers contribute to inventory shortages and overdue orders?",
            managed,
            tool_functions={},
            use_decision_model=False,
        )
        self.assertEqual(captured["route"], "CROSS_DOMAIN")
        self.assertTrue(captured["read_only"])
        self.assertFalse(result["needs_clarification"])
        self.assertEqual(result["answer"]["summary"], "evidence returned")


if __name__ == "__main__":
    unittest.main()
