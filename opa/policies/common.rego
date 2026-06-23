package policy.gate

default decision := {
    "decision": "allow",
    "control_id": null,
    "triggered_controls": [],
    "reason": "No controls triggered",
    "required_approval_role": null,
    "framework_mappings": [],
    "failure_mode": "fail_open",
    "logging_requirements": "standard",
    "policy_version": "0.1.0-trivial",
    "threshold_used": 0.75
}
