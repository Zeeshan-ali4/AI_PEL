from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_event_feed_page_loads_and_references_static_eventsource_js(wired_pipeline):
    client = TestClient(app)
    response = client.get("/events/3")
    assert response.status_code == 200
    html = response.text
    assert "/static/event_feed.js" in html
    assert 'data-stream-url="/run/3/stream"' in html
    assert "event-feed-list" in html
    assert "trace" in html.lower()
    assert "event-row-background" in html
    assert "event-row-focal" in html

    js = client.get("/static/event_feed.js")
    assert js.status_code == 200
    body = js.text
    assert "new EventSource" in body
    assert "event-row-background" in body
    assert "event-row-focal" in body
    assert "decision-allow" in body
    assert "decision-warn" in body
    assert "decision-block" in body
