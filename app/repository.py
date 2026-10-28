from __future__ import annotations

import json
from pathlib import Path

from app.models import Encounter, Observation, PatientRecord


class HealthcareRepository:
    def __init__(self, data_path: Path | None = None) -> None:
        path = data_path or Path(__file__).resolve().parents[1] / "data" / "synthetic_fhir.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        self.patients = [PatientRecord(**item) for item in payload["patients"]]
        self.observations = [Observation(**item) for item in payload["observations"]]
        self.encounters = [Encounter(**item) for item in payload["encounters"]]

    def search_patients(self, query: str, limit: int) -> list[PatientRecord]:
        needle = query.casefold().strip()
        matches = [
            patient
            for patient in self.patients
            if needle in patient.id.casefold()
            or needle in patient.name.given.casefold()
            or needle in patient.name.family.casefold()
        ]
        return matches[:limit]

    def get_patient(self, patient_id: str) -> PatientRecord | None:
        return next((item for item in self.patients if item.id == patient_id), None)

    def patient_observations(self, patient_id: str, code: str | None = None):
        values = [item for item in self.observations if item.patient_id == patient_id]
        if code:
            values = [item for item in values if item.code.casefold() == code.casefold()]
        return sorted(values, key=lambda item: item.effective_date, reverse=True)

    def patient_encounters(self, patient_id: str):
        values = [item for item in self.encounters if item.patient_id == patient_id]
        return sorted(values, key=lambda item: item.date, reverse=True)

