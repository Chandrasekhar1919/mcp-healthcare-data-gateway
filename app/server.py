from __future__ import annotations

import os
from pathlib import Path

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from app.audit import AuditStore
from app.gateway import AccessDeniedError, HealthcareGateway, NotFoundError
from app.models import (
    AccessContext,
    AggregateResult,
    Observation,
    PatientSearchItem,
    PatientSummary,
)
from app.policy import AccessPolicy
from app.repository import HealthcareRepository

ROOT = Path(__file__).resolve().parents[1]
audit_path = Path(os.getenv("AUDIT_DATABASE_PATH", ROOT / "data" / "audit.db"))
gateway = HealthcareGateway(HealthcareRepository(), AccessPolicy(), AuditStore(audit_path))

mcp = MCPServer(
    "Healthcare Data Gateway",
    instructions=(
        "Access synthetic healthcare data through least-privilege tools. Always supply the "
        "requester's identity, role, and purpose. Never treat outputs as medical advice."
    ),
)


def _context(requester_id: str, role: str, purpose: str) -> AccessContext:
    try:
        return AccessContext(requester_id=requester_id, role=role, purpose=purpose)
    except ValueError as exc:
        raise ToolError(f"Invalid access context: {exc}") from exc


def _tool_call(function, *args):
    try:
        return function(*args)
    except (AccessDeniedError, NotFoundError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Search synthetic patient directory")
def search_patients(
    query: str,
    requester_id: str,
    role: str,
    purpose: str,
    limit: int = 10,
) -> list[PatientSearchItem]:
    """Search synthetic patients by ID or name with role-based field redaction."""
    context = _context(requester_id, role, purpose)
    return _tool_call(gateway.search_patients, query, limit, context)


@mcp.tool(title="Get synthetic patient summary")
def get_patient_summary(
    patient_id: str,
    requester_id: str,
    role: str,
    purpose: str,
) -> PatientSummary:
    """Return a policy-gated synthetic summary for treatment coordination."""
    context = _context(requester_id, role, purpose)
    return _tool_call(gateway.patient_summary, patient_id, context)


@mcp.tool(title="List synthetic observations")
def list_observations(
    patient_id: str,
    requester_id: str,
    role: str,
    purpose: str,
    code: str | None = None,
) -> list[Observation]:
    """List recent synthetic observations, optionally filtered by code."""
    context = _context(requester_id, role, purpose)
    return _tool_call(gateway.observations, patient_id, code, context)


@mcp.tool(title="Aggregate synthetic encounters")
def aggregate_encounters(
    requester_id: str,
    role: str,
    purpose: str,
) -> AggregateResult:
    """Return deidentified encounter counts for authorized analysts."""
    context = _context(requester_id, role, purpose)
    return _tool_call(gateway.encounter_counts, context)


@mcp.resource("healthcare://metadata")
def metadata() -> dict[str, str | bool]:
    """Non-sensitive metadata describing the synthetic gateway."""
    return {
        "name": "MCP Healthcare Data Gateway",
        "data": "synthetic FHIR-style resources",
        "clinical_use": False,
        "authentication": "demo access context; use OAuth in production",
    }


@mcp.resource("healthcare://policy/access")
def access_policy() -> str:
    """Human-readable least-privilege access policy."""
    return (
        "Clinicians and care coordinators may access clinical details for treatment. "
        "Receptionists may search the directory with redacted demographics for operations. "
        "Analysts may access deidentified aggregates only. Every allow and deny is audited."
    )


@mcp.prompt(title="Create a care-coordination brief")
def care_coordination_brief(patient_id: str, requester_id: str) -> str:
    """Guide a host to build a grounded brief using the gateway tools."""
    return (
        f"For synthetic patient {patient_id}, call get_patient_summary with requester "
        f"{requester_id!r}, an authorized role, and treatment purpose. Summarize only the "
        "returned facts, cite resource IDs, identify missing data, and include the statement "
        "'Operational support only; not medical advice.'"
    )


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "streamable-http"}:
        raise ValueError("MCP_TRANSPORT must be 'stdio' or 'streamable-http'")
    try:
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()

