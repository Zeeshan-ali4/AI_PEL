from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_event_feed_page_loads_and_references_static_eventsource_js(wired_pipeline):
    client = TestClient(app)
    response = client.get("/events/3")
    assert response.status_code == 200
    html = response.text
    assert "/static/event_feed.js?v=" in html
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
    assert "event-feed-terminal-body" in html
    assert "Connecting to " in body


def test_event_feed_script_src_is_cache_busted(wired_pipeline):
    client = TestClient(app)
    response = client.get("/events/3")
    assert response.status_code == 200
    assert 'src="/static/event_feed.js?v=' in response.text


def test_event_feed_is_discoverable_from_primary_nav_and_scenario_cards(wired_pipeline):
    client = TestClient(app)

    dashboard = client.get("/")
    assert dashboard.status_code == 200
    assert 'href="/events"' in dashboard.text
    assert "Live Feed" in dashboard.text

    scenarios = client.get("/scenarios")
    assert scenarios.status_code == 200
    assert 'href="/events/3"' in scenarios.text
    assert "Run scenario 3 live feed" in scenarios.text
    assert 'action="/scenarios/3/run"' in scenarios.text
    assert "Run decision view only" in scenarios.text
