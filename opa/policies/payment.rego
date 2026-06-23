package policy.gate

import rego.v1

is_payment if {
  input.action.action_type == "financial.payment.issue"
}

payment_amount := amount if {
  amount := input.action.parameters.amount_gbp
}

triggered_control["FIN-PAY-001"] if {
  is_payment
  control_enabled("FIN-PAY-001")
  input.context.customer.fraud_flag == true
}

triggered_control["FIN-PAY-001"] if {
  is_payment
  control_enabled("FIN-PAY-001")
  input.context.customer.sanctions_match == true
}

triggered_control["FIN-PAY-001"] if {
  is_payment
  control_enabled("FIN-PAY-001")
  input.context.customer.status == "blocked"
}

triggered_control["FIN-PAY-002"] if {
  is_payment
  control_enabled("FIN-PAY-002")
  payment_amount > 500
  input.context.approval_state.has_approval == false
}

triggered_control["FIN-PAY-003"] if {
  is_payment
  control_enabled("FIN-PAY-003")
  input.context.payment_history.count_30d >= 3
}

triggered_control["FIN-PAY-004"] if {
  is_payment
  control_enabled("FIN-PAY-004")
  input.context.affects_individual_financial_standing == true
}
