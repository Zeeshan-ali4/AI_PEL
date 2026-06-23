"""Agent simulator for the six canonical T03 scenarios."""

from __future__ import annotations

from typing import Any, Iterator

from app.pep.sdk_wrapper import SDKWrapper
from scenarios.scenarios import get_scenarios


def iter_scenario_tool_calls() -> Iterator[dict[str, Any]]:
    """Yield one raw tool-call dictionary per canonical scenario, in order."""
    for scenario in sorted(get_scenarios(), key=lambda item: item["number"]):
        yield scenario["raw_tool_call"]


def main() -> None:
    wrapper = SDKWrapper()
    for raw_call in iter_scenario_tool_calls():
        print(wrapper.call_tool(raw_call))


if __name__ == "__main__":
    main()
