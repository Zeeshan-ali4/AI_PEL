from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_global_nav_includes_evidence_gap_link_from_existing_pages() -> None:
    client = TestClient(app)

    for path in ("/evidence-gap", "/scenarios"):
        response = client.get(path)
        assert response.status_code == 200
        html = response.text
        assert '<nav class="nav-links" aria-label="Primary navigation">' in html
        assert 'href="/evidence-gap"' in html
        assert "Evidence Gap" in html
