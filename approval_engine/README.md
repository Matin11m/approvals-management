# Approval Engine (Unified Module) - Odoo 19

A single comprehensive addon for generic approval workflows, including per-request Python execute-code rules.

## What this module includes
- Template-based approvals for any Odoo model
- Multi-step approval flow
- Request lifecycle and audit logs
- Binding metadata for model/view/method targeting
- Per-request Python execute-code rules (`safe_eval`, exec mode)

## Documentation
- Technical doc (FA): `approval_engine/docs/unified_module_technical_fa.md`
- User guide (FA): `approval_engine/docs/unified_module_user_guide_fa.md`
- Test scenarios (FA): `approval_engine/docs/unified_module_test_scenarios_fa.md`

## Notes
- This is now a unified approach: no separate `approval_engine_code_rules` module is required.
- Python rules can block approve/reject when `result = False`.
