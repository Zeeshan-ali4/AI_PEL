package policy.gate

import rego.v1

policy_version := "1.0.0-t10"

fail_closed_mappings := [
  "Internal AI Governance Policy (safe-default)",
  "ISO/IEC 42001 (robustness)",
]

threshold := object.get(input.config, "high_confidence_threshold", 0.75)

control_enabled(id) if {
  data.controls[id].enabled == true
  not data.controls[id].proposed == true
}

control_decision(id) := data.controls[id].decision
control_role(id) := data.controls[id].required_approval_role
control_mappings(id) := data.controls[id].framework_mappings
control_reason(id) := data.controls[id].description

fail_closed_triggered if {
  input.context.context_resolution_ok == false
}

fail_closed_triggered if {
  input.evidence.sensor_error == true
}

precedence_rank("fail_closed") := 0
precedence_rank("block") := 1
precedence_rank("escalate") := 2
precedence_rank("require_evidence") := 3
precedence_rank("modify") := 4
precedence_rank("allow_with_logging") := 5
precedence_rank("allow") := 6

ordered_controls := [
  "FIN-PAY-001",
  "FIN-PAY-002",
  "FIN-PAY-003",
  "FIN-PAY-004",
  "COMM-EMAIL-001",
  "COMM-EMAIL-002",
  "COMM-EMAIL-003",
]

triggered_controls := [id |
  id := ordered_controls[_]
  triggered_control[id]
]

selected_rank := min([precedence_rank(control_decision(id)) | id := triggered_controls[_]]) if {
  count(triggered_controls) > 0
}

selected_index := min([i |
  count(triggered_controls) > 0
  id := ordered_controls[i]
  triggered_control[id]
  precedence_rank(control_decision(id)) == selected_rank
])

selected_control := ordered_controls[selected_index] if {
  count(triggered_controls) > 0
}

logging_requirements_for(decision_value) := "enhanced" if {
  decision_value == "allow_with_logging"
}

logging_requirements_for(decision_value) := "enhanced" if {
  decision_value == "fail_closed"
}

logging_requirements_for(decision_value) := "standard" if {
  decision_value != "allow_with_logging"
  decision_value != "fail_closed"
}

fail_closed_decision := {
  "decision": "fail_closed",
  "control_id": null,
  "triggered_controls": ["GLOBAL-FAIL-CLOSED"],
  "reason": "Required policy context or semantic sensor failed; failing closed before execution",
  "required_approval_role": null,
  "framework_mappings": fail_closed_mappings,
  "failure_mode": "fail_closed",
  "logging_requirements": "enhanced",
  "policy_version": policy_version,
  "threshold_used": threshold,
}

selected_decision := {
  "decision": decision_value,
  "control_id": id,
  "triggered_controls": triggered_controls,
  "reason": control_reason(id),
  "required_approval_role": control_role(id),
  "framework_mappings": control_mappings(id),
  "failure_mode": "fail_closed",
  "logging_requirements": logging_requirements_for(decision_value),
  "policy_version": policy_version,
  "threshold_used": threshold,
} if {
  count(triggered_controls) > 0
  id := selected_control
  decision_value := control_decision(id)
}

allow_decision := {
  "decision": "allow",
  "control_id": null,
  "triggered_controls": [],
  "reason": "No controls triggered",
  "required_approval_role": null,
  "framework_mappings": [],
  "failure_mode": "fail_closed",
  "logging_requirements": "standard",
  "policy_version": policy_version,
  "threshold_used": threshold,
}

decision := fail_closed_decision if {
  fail_closed_triggered
}

decision := selected_decision if {
  not fail_closed_triggered
  count(triggered_controls) > 0
}

decision := allow_decision if {
  not fail_closed_triggered
  count(triggered_controls) == 0
}
