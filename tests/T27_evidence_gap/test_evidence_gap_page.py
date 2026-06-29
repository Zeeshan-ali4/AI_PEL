from __future__ import annotations

import re
from html.parser import HTMLParser

from fastapi.testclient import TestClient

from app.main import app


class LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[tuple[str, str]] = []
        self._current_href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            attrs_dict = dict(attrs)
            self._current_href = attrs_dict.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._current_href is not None:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._current_href is not None:
            self.links.append((self._current_href, "".join(self._text).strip()))
            self._current_href = None
            self._text = []


def _page() -> str:
    response = TestClient(app).get("/evidence-gap")
    assert response.status_code == 200
    return response.text


def test_evidence_gap_page_renders_cold() -> None:
    html = _page()

    assert "The evidence gap AI PEL closes" in html
    assert "before execution" in html
    assert "record_hash/example" not in html


def test_evidence_gap_contains_at_least_five_paired_without_with_points() -> None:
    html = _page()

    assert html.count('data-testid="evidence-gap-pair"') >= 5
    assert html.count('data-testid="without-ai-pel"') >= 5
    assert html.count('data-testid="with-ai-pel"') >= 5
    for phrase in [
        "Post-hoc-only visibility",
        "Implicit decision semantics",
        "Context reconstructed later",
        "No chain of custody",
        "Control traceability is unclear",
    ]:
        assert phrase in html


def test_with_ai_pel_points_reference_existing_demo_surfaces_or_fields() -> None:
    html = _page()

    for required in ["/scenarios", "decision.decision", "decision.reason", "context", "evidence"]:
        assert required in html
    concrete_references = ["record_hash", "prev_hash", "framework_mappings", "audit-chain verification", "approval_decision"]
    assert sum(reference in html for reference in concrete_references) >= 4
    forbidden_claims = ["certified compliant", "production audited", "guarantees compliance", "100%"]
    assert not any(claim in html.lower() for claim in forbidden_claims)


def test_evidence_gap_live_link_points_to_working_populated_page() -> None:
    html = _page()
    parser = LinkParser()
    parser.feed(html)
    live_links = [href for href, _ in parser.links if href == "/scenarios"]

    assert live_links
    response = TestClient(app).get(live_links[0])

    assert response.status_code == 200
    assert "Scenario runner" in response.text
    assert len(re.findall(r"Scenario \d+:", response.text)) >= 6
