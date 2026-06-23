import copy
import subprocess
import sys

from app.pep.agent_simulator import iter_scenario_tool_calls
from app.pep.sdk_wrapper import INTERCEPTION_MESSAGE, SDKWrapper


def test_sdk_wrapper_logs_intercepted_before_execution_for_each_call(capsys):
    wrapper = SDKWrapper()
    for call in iter_scenario_tool_calls():
        wrapper.call_tool(call)
    captured = capsys.readouterr()
    assert captured.out.count(INTERCEPTION_MESSAGE) == 6


def test_sdk_wrapper_forwards_raw_call_unchanged_to_placeholder_pipeline():
    wrapper = SDKWrapper()
    calls = list(iter_scenario_tool_calls())
    for original in (calls[0], calls[3]):
        before = copy.deepcopy(original)
        result = wrapper.call_tool(original)
        assert result == before
        assert original == before
        assert result is not original


def test_sdk_wrapper_does_not_report_business_execution_before_forwarding(capsys):
    wrapper = SDKWrapper()
    for call in (list(iter_scenario_tool_calls())[0], list(iter_scenario_tool_calls())[3]):
        result = wrapper.call_tool(call)
        output = capsys.readouterr().out.lower()
        combined = f"{output} {result}".lower()
        assert INTERCEPTION_MESSAGE in output
        for forbidden in ("payment issued", "email sent", "decision enforced", "approval created", "audit record", "executed"):
            assert forbidden not in combined


def test_verify_loop_prints_six_intercepted_raw_calls():
    completed = subprocess.run(
        [sys.executable, "-m", "app.pep.agent_simulator"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.count(INTERCEPTION_MESSAGE) == 6
    assert completed.stdout.count("'scenario_id':") == 6
