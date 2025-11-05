from generic_connections.io import load_connections_yaml


def test_load_yaml_env_expansion(tmp_path, monkeypatch):
    yml = tmp_path / "c.yml"
    yml.write_text(
        "a:\n" "  platform: Postgres\n" "  host: ${H}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("H", "db.local")
    data = load_connections_yaml(str(yml))
    assert data["a"]["host"] == "db.local"
