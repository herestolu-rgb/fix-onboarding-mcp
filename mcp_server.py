"""
mcp_server.py

A real MCP server exposing the FIX validator as MCP tools.
Built on the official Anthropic MCP Python SDK (`mcp` package on PyPI).

Run it directly to start the server over stdio:
    python mcp_server.py

Any MCP-compatible client (Claude Desktop, an MCP inspector, a custom client)
can then connect and call the two tools below.
"""

from typing import Optional

from mcp.server.mcpserver import MCPServer
from fix_validator import (
    ValidationContext,
    parse_execution_report,
    validate_new_order_single,
)

mcp = MCPServer("fix-onboarding-validator")


@mcp.tool()
def validate_new_order_single_tool(
    raw_fix_message: str,
    venue_id: Optional[str] = None,
) -> dict:
    """
    Validate a FIX NewOrderSingle (35=D) message.

    Args:
        raw_fix_message: pipe-delimited FIX tag=value string,
            e.g. "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1"

        venue_id: optional explicit venue-policy authority.
            If supplied, the validator applies the policy bound to that
            venue. FIX message fields such as TargetCompID (56) do not
            implicitly activate venue policy.

    Returns:
        dict with 'valid' (bool), 'verdict' (PASS/FAIL/ESCALATE),
        'decision_layer' (PROTOCOL/POLICY/AUTHORITY when available),
        and either 'parsed' fields or 'errors' list.
    """

    # #004 Checkpoint 3B:
    # Authority enters through explicit caller-supplied context.
    # CompIDs contained in the FIX message remain message data only.
    context = (
        ValidationContext(venue_id=venue_id)
        if venue_id is not None
        else None
    )

    result = validate_new_order_single(
        raw_fix_message,
        context=context,
    )

    return {
        "valid": result.valid,
        "verdict": result.verdict,
        "decision_layer": result.decision_layer,
        "msg_type": result.msg_type,
        "parsed": result.parsed,
        "errors": result.errors,
    }


@mcp.tool()
def parse_execution_report_tool(raw_fix_message: str) -> dict:
    """
    Validate a FIX ExecutionReport (35=8) message.

    Args:
        raw_fix_message: pipe-delimited FIX tag=value string,
            e.g. "8=FIX.4.4|35=8|55=AAPL|39=2|32=1000|31=150.25"

    Returns:
        dict with 'valid' (bool), 'verdict' (PASS/FAIL/ESCALATE),
        and either 'parsed' fields or 'errors' list.
    """
    result = parse_execution_report(raw_fix_message)

    return {
        "valid": result.valid,
        "verdict": result.verdict,
        "msg_type": result.msg_type,
        "parsed": result.parsed,
        "errors": result.errors,
    }


if __name__ == "__main__":
    mcp.run()