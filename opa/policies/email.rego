package policy.gate

import rego.v1

is_email if {
  input.action.action_type == "communication.email.send"
}

external_recipient if {
  input.context.recipient.is_external == true
}

triggered_control["COMM-EMAIL-001"] if {
  is_email
  control_enabled("COMM-EMAIL-001")
  external_recipient
  input.context.recipient.approved_disclosure_basis == false
  input.evidence.contains_special_category_data == true
}

triggered_control["COMM-EMAIL-002"] if {
  is_email
  control_enabled("COMM-EMAIL-002")
  external_recipient
  input.evidence.vulnerability_indicators.present == true
  input.evidence.overall_confidence < threshold
}

triggered_control["COMM-EMAIL-003"] if {
  is_email
  control_enabled("COMM-EMAIL-003")
  external_recipient
  input.evidence.contains_personal_data == true
  input.evidence.contains_special_category_data == false
}
