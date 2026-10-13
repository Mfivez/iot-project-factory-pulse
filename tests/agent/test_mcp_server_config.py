from factorypulse.agent.mcp_server import get_mcp_config


def test_mcp_config_defaults_to_streamable_http(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    assert get_mcp_config() == {
        "transport": "streamable-http",
        "host": "127.0.0.1",
        "port": 8766,
    }
