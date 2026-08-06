"""Verify the MCP surface through a real client, not by reading the module.

FastMCP can connect a client directly to a server object in-process, so this exercises the
actual protocol — schema generation, annotations, resource templates — without a transport
or a network. That matters because the things most likely to be wrong here are not the
Python (mypy covers that) but the *protocol surface*: a tool whose schema will not
generate, an annotation a client ignores, a resource template whose URI does not parse.

None of these tests touch Snowflake. They assert what the server advertises, which is what
an MCP client sees before it calls anything.

    uv run --extra mcp pytest mcp/tests -q
"""

from __future__ import annotations

import pytest
from fastmcp import Client
from warrant_mcp.server import GOVERNED_OBJECTS, mcp

READ_ONLY = {
    "governance_posture",
    "authority_manifest",
    "what_if_reclassified",
    "replay_decisions",
    "pending_approvals",
    "refusal_ledger",
    "decision_log",
    "search_runbooks",
    "detect_exceptions",
    "read_runbook",
    "task_activity",
}

ACTING = {"run_agent_loop", "execute_approved_action"}


@pytest.fixture
async def client():
    """An in-process MCP client attached to the server."""
    async with Client(mcp) as connected:
        yield connected


async def test_every_tool_is_advertised(client):
    """The surface is exactly what is intended — no more, and nothing missing."""
    names = {tool.name for tool in await client.list_tools()}
    assert names == READ_ONLY | ACTING


async def test_reads_are_annotated_read_only(client):
    """A client must be able to tell which tools cannot change anything.

    This is what lets an MCP host auto-approve reads and prompt on writes. Getting it wrong
    in the permissive direction means a host silently runs an action.
    """
    for tool in await client.list_tools():
        if tool.name in READ_ONLY:
            assert tool.annotations is not None, f"{tool.name} carries no annotations"
            assert tool.annotations.readOnlyHint is True, f"{tool.name} is not marked read-only"


async def test_the_executor_is_marked_destructive(client):
    """The one tool that can change a system says so, in the field clients check."""
    execute = next(t for t in await client.list_tools() if t.name == "execute_approved_action")
    assert execute.annotations is not None
    assert execute.annotations.readOnlyHint is False
    assert execute.annotations.destructiveHint is True


async def test_no_tool_accepts_a_tier():
    """The load-bearing assertion in this file.

    Authority is resolved from the object tags. If any tool took a tier, a caller could ask
    to run at one — and the whole argument of the project would be a convention rather than
    a control. This asserts the *schema* offers no way to express it, so it holds against a
    persuaded model rather than only against a well-behaved one.
    """
    async with Client(mcp) as client:
        for tool in await client.list_tools():
            properties = (tool.inputSchema or {}).get("properties", {})
            for field in properties:
                assert "tier" not in field.lower(), f"{tool.name} exposes {field}"
                assert "authority" not in field.lower(), f"{tool.name} exposes {field}"
                assert "force" not in field.lower(), f"{tool.name} exposes {field}"


async def test_instructions_state_the_two_counter_intuitive_rules(client):
    """The server's instructions are part of the product, so they are asserted.

    A model driving this needs to know two things that contradict its defaults: it cannot
    choose its own authority, and a refusal is a result rather than an error to route
    around. If either sentence is edited away, this fails.
    """
    instructions = mcp.instructions or ""
    assert "cannot choose an action's authority" in instructions
    assert "A refusal is a result, not an error" in instructions
    assert "untagged" in instructions.lower()


async def test_resources_and_their_tool_twins(client):
    """Every resource is reachable as a tool too.

    Most MCP clients — CoCo included — surface only tools to the model. A resource with no
    tool twin is documentation rather than a capability, so the pairing is asserted rather
    than left to memory.
    """
    uris = {str(resource.uri) for resource in await client.list_resources()}
    assert uris == {
        "warrant://governance/tags",
        "warrant://capabilities",
        "warrant://audit/recent",
        "warrant://runbooks",
    }

    templates = {t.uriTemplate for t in await client.list_resource_templates()}
    assert templates == {"warrant://runbooks/{doc_id}"}

    tools = {tool.name for tool in await client.list_tools()}
    for twin in ("governance_posture", "authority_manifest", "decision_log", "read_runbook"):
        assert twin in tools


async def test_what_if_rejects_an_object_warrant_does_not_govern(client):
    """An unknown object is refused before any connection is attempted.

    Also confirms the allowlist and the governed-object tuple have not drifted apart: the
    error names the tool that lists them.
    """
    result = await client.call_tool(
        "what_if_reclassified",
        {"obj": "WARRANT.DATA.NOT_A_TABLE", "sensitivity": "regulated"},
        raise_on_error=False,
    )
    assert result.is_error
    assert "not governed" in str(result.content[0].text)


def test_governed_objects_are_fully_qualified():
    """A bare tag name raises 'Tag does not exist or not authorized' at runtime.

    The tag lives in CORE while the tables live in DATA, so SYSTEM$GET_TAG needs the full
    path. Cheap to assert here; expensive to discover from a Snowflake error message.
    """
    for fqn in GOVERNED_OBJECTS:
        assert fqn.count(".") == 2, f"{fqn} is not fully qualified"
        assert fqn.startswith("WARRANT.")
