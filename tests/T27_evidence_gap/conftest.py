from __future__ import annotations

import pytest

from app.web.routes import templates


@pytest.fixture(autouse=True)
def no_pending_escalation_db_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep static/nav page tests cold-start and independent of audit storage."""

    monkeypatch.setitem(templates.env.globals, "pending_escalation_count", lambda: 0)
