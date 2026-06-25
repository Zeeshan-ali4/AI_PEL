from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.main import app


def parse_sse_events(body: str) -> list[dict]:
    events = []
    for raw_block in body.split("\n\n"):
        block = raw_block.strip()
        if not block:
            continue
        for line in block.splitlines():
            if line.startswith("data:"):
                events.append(json.loads(line[len("data:") :].strip()))
    return events


def stream_scenario(scenario_id: int) -> list[dict]:
    client = TestClient(app)
    with client.stream("GET", f"/run/{scenario_id}/stream") as response:
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
        body = "".join(response.iter_text())
    return parse_sse_events(body)
