from pathlib import Path


def test_deploy_doc_mentions_tls_and_port_443():
    content = Path("docs/specs/deployment.md").read_text()
    assert "443" in content
    assert "HTTPS" in content
    assert "reverse proxy" in content.lower()
