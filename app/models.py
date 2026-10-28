from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Role(StrEnum):
    CLINICIAN = "clinician"
    CARE_COORDINATOR = "care_coordinator"
    RECEPTIONIST = "receptionist"
    ANALYST = "analyst"


class Purpose(StrEnum):
    TREATMENT = "treatment"
    OPERATIONS = "operations"
    ANALYTICS = "analytics"


class AccessContext(BaseModel):
    requester_id: str = Field(min_length=3, max_length=80)
    role: Role
    purpose: Purpose


class HumanName(BaseModel):
    given: str
    family: str


class PatientRecord(BaseModel):
    resource_type: str = "Patient"
    id: str
    name: HumanName
    birth_date: str
    administrative_gender: str
    city: str
    active: bool


class Observation(BaseModel):
    resource_type: str = "Observation"
    id: str
    patient_id: str
    code: str
    display: str
    value: str
    effective_date: str


class Encounter(BaseModel):
    resource_type: str = "Encounter"
    id: str
    patient_id: str
    encounter_type: str
    status: str
    date: str
    department: str


class PatientSearchItem(BaseModel):
    patient_id: str
    display_name: str
    birth_year: int | None = None
    city: str | None = None


class PatientSummary(BaseModel):
    patient_id: str
    display_name: str
    demographics: dict[str, str | bool]
    recent_observations: list[Observation]
    recent_encounters: list[Encounter]
    data_classification: str = "synthetic-restricted"


class AggregateResult(BaseModel):
    metric: str
    groups: dict[str, int]
    total: int
    deidentified: bool = True


class AuditEvent(BaseModel):
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    requester_id: str
    role: Role
    purpose: Purpose
    operation: str
    target: str
    decision: str
    reason: str

