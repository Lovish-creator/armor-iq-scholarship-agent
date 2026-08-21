# Threat Model & Security Policy

## Assets Protected
1. **Student Authority**: Preventing AI agent from taking unauthorized actions on behalf of the student.
2. **Student Identity Data**: Protecting student certificates, domicile proof, and marksheet data.
3. **Application Integrity**: Ensuring submitted applications strictly conform to eligible, authorized scholarships.

## Threat Vectors & Countermeasures

| Threat Vector | Description | Countermeasure | Security Evidence |
| :--- | :--- | :--- | :--- |
| **Agent Reasoning Drift** | Autonomous agent reasons that applying to private scholarships will increase student funding, violating user prompt. | ArmorIQ `capture_plan` locks intent constraints (`type: government`). Target action checked against signed token. | ArmorIQ throws `IntentMismatchException`. `submit_application` tool aborted. |
| **Bypass of Tool Layer** | Agent attempts direct API submission without token. | Mock Portal API requires `intent_token` and `armoriq_decision == ALLOW`. | HTTP 403 Forbidden raised. Non-execution count = 0. |
| **Falsification of Profile** | Agent attempts to modify student income or state parameter to force eligibility. | ArmorIQ policy check verifies inputs against canonical plan profile. | Action blocked prior to portal API dispatch. |
