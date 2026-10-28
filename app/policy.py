from __future__ import annotations

from dataclasses import dataclass

from app.models import AccessContext, Purpose, Role


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


class AccessPolicy:
    """Purpose- and role-based rules kept separate from transport and storage."""

    def patient_search(self, context: AccessContext) -> Decision:
        if context.role == Role.ANALYST:
            return Decision(False, "Analysts may use aggregate tools only")
        if context.purpose not in {Purpose.TREATMENT, Purpose.OPERATIONS}:
            return Decision(False, "Patient search requires treatment or operations purpose")
        return Decision(True, "Role and purpose permit patient directory search")

    def clinical_detail(self, context: AccessContext) -> Decision:
        if context.role not in {Role.CLINICIAN, Role.CARE_COORDINATOR}:
            return Decision(False, "Clinical details require a clinical coordination role")
        if context.purpose != Purpose.TREATMENT:
            return Decision(False, "Clinical details require treatment purpose")
        return Decision(True, "Treatment access permitted for clinical role")

    def aggregate(self, context: AccessContext) -> Decision:
        if context.role != Role.ANALYST or context.purpose != Purpose.ANALYTICS:
            return Decision(False, "Aggregate analytics require analyst role and analytics purpose")
        return Decision(True, "Deidentified aggregate access permitted")

