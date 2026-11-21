from types import SimpleNamespace
import pytest
from data_harness.governance import BigQuerySchemaDiscovery, ReadOnlyQueryValidator, build_evidence_provenance


def test_schema_discovery_is_allow_listed():
    class Client:
        def get_table(self, table_id):
            return SimpleNamespace(table_type="VIEW", schema=[SimpleNamespace(name="product_id", field_type="STRING", mode="REQUIRED", description="Product key")])
    discovery = BigQuerySchemaDiscovery(Client(), "p", "d", ("v_inventory_product_risk",))
    result = discovery.discover("v_inventory_product_risk")
    assert result.columns[0].name == "product_id"
    with pytest.raises(PermissionError):
        discovery.discover("suppliers")


def test_query_validator_approves_only_bounded_select_from_approved_view():
    validator = ReadOnlyQueryValidator("p", "d", ("v_inventory_product_risk",))
    result = validator.validate("SELECT product_id FROM `p.d.v_inventory_product_risk` LIMIT 10")
    assert result.approved
    assert result.referenced_objects == ("p.d.v_inventory_product_risk",)


@pytest.mark.parametrize("sql", [
    "DELETE FROM `p.d.v_inventory_product_risk` WHERE TRUE",
    "SELECT * FROM `p.d.suppliers` LIMIT 10",
    "SELECT * FROM `p.d.v_inventory_product_risk`",
    "SELECT * FROM `p.d.v_inventory_product_risk` LIMIT 10; SELECT 1",
    "SELECT * FROM EXTERNAL_QUERY('x','select 1') LIMIT 10",
])
def test_query_validator_rejects_unsafe_or_unbounded_sql(sql):
    validator = ReadOnlyQueryValidator("p", "d", ("v_inventory_product_risk",))
    assert not validator.validate(sql).approved


def test_provenance_hashes_query_and_captures_metric_contract():
    record = build_evidence_provenance(
        metric={"id": "inventory.shortage_units", "name": "Shortage units", "unit": "units", "entity_grain": "product"},
        source_view="v_inventory_risk_summary", sql="SELECT 1", row_count=1,
        validation_checks=("read_only",),
    )
    assert len(record["query_sha256"]) == 64
    assert record["metric_id"] == "inventory.shortage_units"
    assert record["read_only"] is True
