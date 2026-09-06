"""
mcp_server.py

A real MCP server exposing the FIX validator as MCP tools.
Built on the official Anthropic MCP Python SDK (`mcp` package on PyPI).

Run it directly to start the server over stdio:
    python mcp_server.py

Any MCP-compatible client (Claude Desktop, an MCP inspector, a custom client)
can then connect and call the two tools below.
"""

from mcp.server.mcpserver import MCPServer
from fix_validator import validate_new_order_single, parse_execution_report

mcp = MCPServer("fix-onboarding-validator")


@mcp.tool()
def validate_new_order_single_tool(raw_fix_message: str) -> dict:
    """
    Validate a FIX NewOrderSingle (35=D) message.

    Args:
        raw_fix_message: pipe-delimited FIX tag=value string,
            e.g. "8=FIX.4.4|35=D|55=AAPL|54=1|38=1000|40=2|44=150.25|11=ORD1"

    Returns:
        dict with 'valid' (bool), and either 'parsed' fields or 'errors' list.
    """
    result = validate_new_order_single(raw_fix_message)
    return {
        "valid": result.valid,
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
        dict with 'valid' (bool), and either 'parsed' fields or 'errors' list.
    """
    result = parse_execution_report(raw_fix_message)
    return {
        "valid": result.valid,
        "msg_type": result.msg_type,
        "parsed": result.parsed,
        "errors": result.errors,
    }


if __name__ == "__main__":
    mcp.run()
