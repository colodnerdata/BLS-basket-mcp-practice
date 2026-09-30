from bls_escalation_mcp.server import create_server


def test_server_instantiates_and_exposes_core_tools() -> None:
    server = create_server()
    assert server is not None
    assert hasattr(server, "tool")
