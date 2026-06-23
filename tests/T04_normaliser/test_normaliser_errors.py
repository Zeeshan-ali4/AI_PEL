"""Error-path tests for action normalisation."""

from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from app.normaliser.normaliser import UnsupportedToolError, normalise
from scenarios.scenarios import get_raw_tool_call


def test_invalid_enforcement_mode_is_rejected_by_schema() -> None:
    raw_call = deepcopy(get_raw_tool_call(1))
    raw_call["enforcement_mode"] = "invalid-mode"

    with pytest.raises(ValidationError) as error:
        normalise(raw_call)

    assert "enforcement_mode" in str(error.value)
    assert "invalid-mode" in str(error.value)


def test_unknown_tool_name_raises_clear_error() -> None:
    raw_call = deepcopy(get_raw_tool_call(1))
    raw_call["tool_name"] = "unknown_tool"

    with pytest.raises(UnsupportedToolError) as error:
        normalise(raw_call)

    assert "Unsupported tool_name 'unknown_tool'" in str(error.value)


def test_missing_tool_name_raises_clear_error() -> None:
    raw_call = deepcopy(get_raw_tool_call(1))
    raw_call.pop("tool_name")

    with pytest.raises(UnsupportedToolError) as error:
        normalise(raw_call)

    assert "tool_name" in str(error.value)
