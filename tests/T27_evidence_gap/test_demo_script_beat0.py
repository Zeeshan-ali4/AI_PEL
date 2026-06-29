from __future__ import annotations

import re
from pathlib import Path

SCRIPT = Path("DEMO_SCRIPT.md")


def _script() -> str:
    return SCRIPT.read_text()


def _beat_body(script: str, number: int) -> str:
    match = re.search(rf"^## Beat {number} — .*?(?=^## Beat \d+ — |\Z)", script, flags=re.M | re.S)
    assert match is not None
    return match.group(0)


def test_demo_script_adds_beat0_before_dashboard_calm() -> None:
    script = _script()

    assert script.index("## Beat 0") < script.index("## Beat 1 — Dashboard calm")
    beat0 = _beat_body(script, 0)
    assert "Before we look at the system" in beat0
    assert "/evidence-gap" in beat0
    assert "structural rather than reconstructed" in beat0


def test_demo_script_beat_numbers_are_sequential_and_references_consistent() -> None:
    script = _script()
    numbers = [int(number) for number in re.findall(r"^## Beat (\d+) —", script, flags=re.M)]

    assert numbers == list(range(numbers[-1] + 1))
    assert "## Beat 1 — Dashboard calm" in script

    heading_numbers = set(numbers)
    referenced_numbers = {int(number) for number in re.findall(r"\bBeat (\d+)\b", script) if f"## Beat {number} —" not in script}
    assert referenced_numbers <= heading_numbers


def test_demo_script_beat0_is_short_framing_not_new_demo_flow() -> None:
    beat0 = _beat_body(_script(), 0)

    assert len(re.findall(r"\b\w+\b", beat0)) < 170
    forbidden = ["Run Scenario", "Scenario 1", "Scenario 2", "certified", "production-audited", "100%"]
    assert not any(term in beat0 for term in forbidden)
