from pathlib import Path

import pytest

from app.audit import AuditStore
from app.gateway import HealthcareGateway
from app.policy import AccessPolicy
from app.repository import HealthcareRepository


@pytest.fixture
def gateway(tmp_path: Path) -> HealthcareGateway:
    return HealthcareGateway(
        HealthcareRepository(),
        AccessPolicy(),
        AuditStore(tmp_path / "audit.db"),
    )

