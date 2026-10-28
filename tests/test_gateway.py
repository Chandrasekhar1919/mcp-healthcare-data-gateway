import pytest

from app.gateway import AccessDeniedError, NotFoundError
from app.models import AccessContext


def context(role: str, purpose: str) -> AccessContext:
    return AccessContext(requester_id="test-user", role=role, purpose=purpose)


def test_clinician_can_read_patient_summary(gateway):
    summary = gateway.patient_summary("SYN-P001", context("clinician", "treatment"))
    assert summary.patient_id == "SYN-P001"
    assert summary.recent_observations
    assert gateway.audit.count("allow") == 1


def test_receptionist_search_is_redacted(gateway):
    matches = gateway.search_patients("Avery", 5, context("receptionist", "operations"))
    assert matches[0].patient_id == "SYN-P001"
    assert matches[0].birth_year is None
    assert matches[0].city is None


def test_analyst_cannot_search_identifiable_patients(gateway):
    with pytest.raises(AccessDeniedError, match="aggregate tools only"):
        gateway.search_patients("Avery", 5, context("analyst", "analytics"))
    assert gateway.audit.count("deny") == 1


def test_analyst_can_read_deidentified_aggregates(gateway):
    result = gateway.encounter_counts(context("analyst", "analytics"))
    assert result.deidentified is True
    assert result.total == 4
    assert result.groups["Primary Care"] == 2


def test_missing_patient_is_explicit_and_audited(gateway):
    with pytest.raises(NotFoundError, match="was not found"):
        gateway.patient_summary("SYN-MISSING", context("clinician", "treatment"))
    assert gateway.audit.count("allow") == 1


def test_observations_can_be_filtered(gateway):
    values = gateway.observations(
        "SYN-P001", "heart-rate", context("care_coordinator", "treatment")
    )
    assert [item.code for item in values] == ["heart-rate"]

