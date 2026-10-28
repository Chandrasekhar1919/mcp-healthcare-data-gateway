from __future__ import annotations

from collections import Counter

from app.audit import AuditStore
from app.models import (
    AccessContext,
    AggregateResult,
    PatientSearchItem,
    PatientSummary,
    Role,
)
from app.policy import AccessPolicy, Decision
from app.repository import HealthcareRepository


class AccessDeniedError(PermissionError):
    pass


class NotFoundError(LookupError):
    pass


class HealthcareGateway:
    def __init__(
        self,
        repository: HealthcareRepository,
        policy: AccessPolicy,
        audit: AuditStore,
    ) -> None:
        self.repository = repository
        self.policy = policy
        self.audit = audit

    def _authorize(
        self,
        context: AccessContext,
        decision: Decision,
        operation: str,
        target: str,
    ) -> None:
        self.audit.record(context, operation, target, decision.allowed, decision.reason)
        if not decision.allowed:
            raise AccessDeniedError(decision.reason)

    def search_patients(
        self, query: str, limit: int, context: AccessContext
    ) -> list[PatientSearchItem]:
        self._authorize(
            context,
            self.policy.patient_search(context),
            "search_patients",
            "directory",
        )
        patients = self.repository.search_patients(query, min(max(limit, 1), 20))
        include_limited_demographics = context.role != Role.RECEPTIONIST
        return [
            PatientSearchItem(
                patient_id=item.id,
                display_name=f"{item.name.given} {item.name.family}",
                birth_year=int(item.birth_date[:4]) if include_limited_demographics else None,
                city=item.city if include_limited_demographics else None,
            )
            for item in patients
        ]

    def patient_summary(self, patient_id: str, context: AccessContext) -> PatientSummary:
        self._authorize(
            context,
            self.policy.clinical_detail(context),
            "get_patient_summary",
            patient_id,
        )
        patient = self.repository.get_patient(patient_id)
        if not patient:
            raise NotFoundError(f"Synthetic patient {patient_id!r} was not found")
        return PatientSummary(
            patient_id=patient.id,
            display_name=f"{patient.name.given} {patient.name.family}",
            demographics={
                "birth_date": patient.birth_date,
                "administrative_gender": patient.administrative_gender,
                "city": patient.city,
                "active": patient.active,
            },
            recent_observations=self.repository.patient_observations(patient.id)[:5],
            recent_encounters=self.repository.patient_encounters(patient.id)[:5],
        )

    def observations(self, patient_id: str, code: str | None, context: AccessContext):
        self._authorize(
            context,
            self.policy.clinical_detail(context),
            "list_observations",
            patient_id,
        )
        if not self.repository.get_patient(patient_id):
            raise NotFoundError(f"Synthetic patient {patient_id!r} was not found")
        return self.repository.patient_observations(patient_id, code)

    def encounter_counts(self, context: AccessContext) -> AggregateResult:
        self._authorize(
            context, self.policy.aggregate(context), "aggregate_encounters", "all-patients"
        )
        groups = Counter(item.department for item in self.repository.encounters)
        return AggregateResult(
            metric="encounters_by_department",
            groups=dict(sorted(groups.items())),
            total=sum(groups.values()),
        )

