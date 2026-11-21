import tempfile
import unittest
from pathlib import Path

from data_harness.core import GovernedDataHarness, HarnessPolicy, SemanticCatalogue


class FakeAdapter:
    source_name = "bigquery"
    def fetch_metric(self, metric_id, parameters):
        return {"source": self.source_name, "metric_id": metric_id, "rows": [{"shortage_units": 572}]}


class DataHarnessTests(unittest.TestCase):
    def test_semantic_resolution_policy_and_adapter(self):
        catalogue_path = Path(__file__).parents[1] / "semantic_catalogue" / "metrics.json"
        catalogue = SemanticCatalogue(catalogue_path)
        metric_id = "inventory.shortage_units"
        harness = GovernedDataHarness(
            catalogue,
            {"bigquery": FakeAdapter()},
            HarnessPolicy(allowed_sources=("bigquery",), allowed_metric_ids=(metric_id,), read_only=True),
        )
        result = harness.retrieve(metric_id, parameters={"limit": 5})
        self.assertEqual(result["metric"]["unit"], "units")
        self.assertEqual(result["evidence"]["rows"][0]["shortage_units"], 572)
        self.assertTrue(result["policy"]["read_only"])

    def test_agent_tool_invocation_passes_through_harness(self):
        catalogue_path = Path(__file__).parents[1] / "semantic_catalogue" / "metrics.json"
        metric_id = "inventory.shortage_units"
        harness = GovernedDataHarness(
            SemanticCatalogue(catalogue_path),
            {"bigquery": FakeAdapter()},
            HarnessPolicy(allowed_sources=("bigquery",), allowed_metric_ids=(metric_id,), read_only=True),
        )
        called = {}
        def tool(limit=10):
            called["limit"] = limit
            return {"rows": [{"shortage_units": 572}]}
        result = harness.invoke_tool(metric_id, tool, {"limit": 5})
        self.assertEqual(called["limit"], 5)
        self.assertEqual(result["metric"]["id"], metric_id)
        self.assertTrue(result["policy"]["read_only"])

    def test_disallowed_source_is_rejected_before_adapter_call(self):
        catalogue_path = Path(__file__).parents[1] / "semantic_catalogue" / "metrics.json"
        harness = GovernedDataHarness(
            SemanticCatalogue(catalogue_path),
            {"bigquery": FakeAdapter()},
            HarnessPolicy(allowed_sources=("bigquery",), allowed_metric_ids=("inventory.shortage_units",)),
        )
        with self.assertRaises(PermissionError):
            harness.retrieve("inventory.shortage_units", source_name="unapproved_source")

    def test_unknown_metric_is_rejected(self):
        catalogue_path = Path(__file__).parents[1] / "semantic_catalogue" / "metrics.json"
        harness = GovernedDataHarness(SemanticCatalogue(catalogue_path), {"bigquery": FakeAdapter()}, HarnessPolicy())
        with self.assertRaises(KeyError):
            harness.retrieve("inventory.not_a_real_metric")


if __name__ == "__main__":
    unittest.main()
