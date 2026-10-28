from __future__ import annotations

import os

import anyio
from mcp import Client

from app.server import mcp


async def run() -> None:
    target = os.getenv("MCP_URL") or mcp
    async with Client(target, raise_exceptions=True) as client:
        tools = await client.list_tools()
        result = await client.call_tool(
            "search_patients",
            {
                "query": "Avery",
                "requester_id": "demo-clinician",
                "role": "clinician",
                "purpose": "treatment",
                "limit": 5,
            },
        )
        assert not result.is_error
        assert result.structured_content["result"][0]["patient_id"] == "SYN-P001"
        print(
            {
                "protocol_version": client.protocol_version,
                "tools": [tool.name for tool in tools.tools],
                "search_result": result.structured_content,
            }
        )


if __name__ == "__main__":
    anyio.run(run)

