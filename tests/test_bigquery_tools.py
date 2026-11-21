import unittest

from tools.bigquery_tools import SupplyChainBigQueryTools


class FakeRow(dict):
    pass


class FakeJob:
    def __init__(self, rows):
        self.rows = rows

    def result(self):
        return self.rows


class FakeClient:
    def __init__(self):
        self.calls = []

    def query(self, sql, job_config=None, location=None):
        self.calls.append((sql, job_config, location))
        return FakeJob([FakeRow({"product_id": "P-001", "inventory_value_at_risk_gbp": 12.5})])


class BigQueryToolTests(unittest.TestCase):
    def setUp(self):
        self.client = FakeClient()
        self.tools = SupplyChainBigQueryTools("demo-project", client=self.client)

    def test_inventory_query_uses_fixed_view_and_caps_limit(self):
        result = self.tools.inventory_risk(inventory_status="CRITICAL", limit=999)
        sql, config, location = self.client.calls[-1]
        self.assertIn("v_inventory_product_risk", sql)
        self.assertIn("LIMIT 100", sql)
        self.assertNotIn("CRITICAL", sql)  # value is a query parameter, not SQL text
        self.assertEqual(result["row_count"], 1)
        self.assertTrue(result["read_only"])
        self.assertEqual(location, "US")

    def test_invalid_filter_rejected_before_query(self):
        with self.assertRaises(ValueError):
            self.tools.inventory_risk(inventory_status="DROP TABLE")
        self.assertEqual(self.client.calls, [])

    def test_identifier_validation(self):
        with self.assertRaises(ValueError):
            SupplyChainBigQueryTools("demo-project;DROP", client=self.client)

    def test_fulfilment_query_defaults_to_overdue_only(self):
        self.tools.fulfillment_exposure()
        sql, config, _ = self.client.calls[-1]
        self.assertIn("is_overdue_open_order", sql)
        self.assertNotIn("DELAYED", sql)


if __name__ == "__main__":
    unittest.main()
