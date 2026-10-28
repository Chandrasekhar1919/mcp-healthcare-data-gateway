import pytest
from mcp import Client

from app.server import mcp


@pytest.mark.anyio
async def test_server_exposes_tools_resources_and_prompt():
    async with Client(mcp, raise_exceptions=True) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

    assert {item.name for item in tools.tools} == {
        "search_patients",
        "get_patient_summary",
        "list_observations",
        "aggregate_encounters",
    }
    assert {str(item.uri) for item in resources.resources} == {
        "healthcare://metadata",
        "healthcare://policy/access",
    }
    assert [item.name for item in prompts.prompts] == ["care_coordination_brief"]


@pytest.mark.anyio
async def test_tool_returns_structured_patient_data():
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "get_patient_summary",
            {
                "patient_id": "SYN-P001",
                "requester_id": "test-clinician",
                "role": "clinician",
                "purpose": "treatment",
            },
        )

    assert result.is_error is False
    assert result.structured_content["patient_id"] == "SYN-P001"
    assert result.structured_content["data_classification"] == "synthetic-restricted"


@pytest.mark.anyio
async def test_denied_tool_call_is_an_mcp_tool_error():
    async with Client(mcp) as client:
        result = await client.call_tool(
            "get_patient_summary",
            {
                "patient_id": "SYN-P001",
                "requester_id": "test-analyst",
                "role": "analyst",
                "purpose": "analytics",
            },
        )

    assert result.is_error is True
    assert "clinical coordination role" in result.content[0].text


@pytest.mark.anyio
async def test_metadata_resource_is_non_sensitive():
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.read_resource("healthcare://metadata")
    assert "synthetic FHIR-style resources" in result.contents[0].text

