from generic_connections.io.LoadConnectionsYaml import load_connections_yaml

def test_load_yaml_env_expansion(tmp_path, monkeypatch):
    y = tmp_path/"c.yml"
    y.write_text("a:
  platform: Postgres
  host: ${H}
")
    monkeypatch.setenv("H", "db.local")
    data = load_connections_yaml(str(y))
    assert data["a"]["host"] == "db.local"
