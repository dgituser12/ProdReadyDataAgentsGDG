from types import SimpleNamespace

from integrations.decision1 import assess_supply_chain_exception


class FakeDecisions:
    def __init__(self, answers=None, error=None):
        self.answers = answers
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(answers=self.answers)


class FakeClient:
    def __init__(self, answers=None, error=None):
        self.decisions = FakeDecisions(answers, error)


def answers(route_conf=0.93, urgent_conf=0.91, severity_conf=0.89):
    return {
        "route": SimpleNamespace(choice="INVENTORY_RISK", confidence=route_conf),
        "urgent": SimpleNamespace(noul=0.94, confidence=urgent_conf),
        "severity": SimpleNamespace(score=4, confidence=severity_conf),
    }


def test_one_dossier_one_request_three_typed_questions():
    client = FakeClient(answers())
    result = assess_supply_chain_exception("Product P-1042 has a 120-unit shortage.", client)
    assert result.route == "INVENTORY_RISK"
    assert result.urgent is True
    assert result.severity == 5
    assert result.source == "gemini_decision_1"
    assert len(client.decisions.calls) == 1
    call = client.decisions.calls[0]
    assert set(call["questions"]) == {"route", "urgent", "severity"}
    assert call["questions"]["route"]["type"] == "choice"
    assert call["questions"]["urgent"]["type"] == "noul"
    assert call["questions"]["severity"]["type"] == "score"
    assert len(call["questions"]["severity"]["criteria"]) == 5
    assert call["questions"]["urgent"]["type"] == "noul"
    assert result.reason.find("P(yes)") >= 0


def test_low_confidence_falls_back_and_does_not_emit_untrusted_fields():
    client = FakeClient(answers(route_conf=0.40))
    result = assess_supply_chain_exception("Inventory shortage for product P-1042", client)
    assert result.source == "local_fallback_low_confidence"
    assert result.route == "INVENTORY_RISK"
    assert result.urgent is None
    assert result.severity is None


def test_api_error_falls_back_without_blocking():
    client = FakeClient(error=TimeoutError())
    result = assess_supply_chain_exception("Overdue fulfilment orders", client)
    assert result.source == "local_fallback_error"
    assert result.route == "FULFILMENT_DELAY"
    assert result.urgent is None
    assert result.severity is None


def test_noul_probability_is_converted_to_boolean_using_threshold():
    payload = answers()
    payload["urgent"] = SimpleNamespace(noul=0.12, confidence=0.91)
    result = assess_supply_chain_exception("Product P-1042 has a 120-unit shortage.", FakeClient(payload))
    assert result.source == "gemini_decision_1"
    assert result.urgent is False
