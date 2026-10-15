from factorypulse.agent.mcp_server import get_mcp_config, load_env_file


def test_mcp_config_defaults_to_streamable_http(monkeypatch):
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    assert get_mcp_config() == {
        "transport": "streamable-http",
        "host": "127.0.0.1",
        "port": 8766,
    }


def test_load_env_file_populates_os_environ(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# Commentaire\n"
        "MCP_TRANSPORT=sse\n"
        "MCP_HOST=0.0.0.0 # ecoute sur toutes les interfaces\n"
        "MCP_PORT=8999\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("MCP_TRANSPORT", raising=False)
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    loaded = load_env_file(env_file)

    assert loaded["MCP_HOST"] == "0.0.0.0"
    assert loaded["MCP_TRANSPORT"] == "sse"
    assert loaded["MCP_PORT"] == "8999"

    config = get_mcp_config(load_env=True, env_path=env_file)
    assert config == {
        "transport": "sse",
        "host": "0.0.0.0",
        "port": 8999,
    }


def test_load_env_file_does_not_override_existing_by_default(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text("MCP_HOST=0.0.0.0\n", encoding="utf-8")

    monkeypatch.setenv("MCP_HOST", "192.168.1.100")
    load_env_file(env_file, override=False)

    assert get_mcp_config()["host"] == "192.168.1.100"

