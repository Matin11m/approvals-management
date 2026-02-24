# End-to-end test scenario: Studio Approval Python Condition

## Goal
Verify that a Studio approval rule can be applied based on Python code and that the readonly guide text helps users write valid code.

## Preconditions
1. Odoo instance is running.
2. `web_studio` and `studio_approval_python_condition` modules are installed.
3. Test users:
   - `Approver`
   - `Requester`
4. A model with approvals enabled (example: Sales Order / `sale.order`).

## Scenario A — UI guide visibility
1. Open **Studio > Approvals** and create/edit an approval rule.
2. Locate the new readonly field **Python Guide** below the domain field.
3. Confirm the guide shows available variables: `env`, `user`, `record`, `rule`, `result`.
4. Confirm the editable field **Python Condition** is visible and empty by default.

### Expected result
- Guide is visible and readonly.
- Python Condition remains editable.

## Scenario B — Positive applicability check
1. Configure a rule on Sales Order confirmation with:
   - Domain: empty
   - Python Condition:
     ```python
     result = record.amount_total > 10000
     ```
2. Create Sales Order `SO-LOW` with total `< 10000`.
3. Try confirming `SO-LOW`.
4. Create Sales Order `SO-HIGH` with total `> 10000`.
5. Try confirming `SO-HIGH` as `Requester`.

### Expected result
- `SO-LOW`: rule is not applicable, no approval block from this rule.
- `SO-HIGH`: rule is applicable and approval flow starts (request/approval needed).

## Scenario C — Syntax validation
1. Edit the same rule.
2. Enter invalid Python code:
   ```python
   result = (record.amount_total > 10000
   ```
3. Save rule.

### Expected result
- Validation error appears (`Invalid python condition syntax`).
- Rule is not saved with invalid code.

## Scenario D — Combined Domain + Python
1. Set Domain to one company only (example current company).
2. Set Python Condition:
   ```python
   result = user.has_group('sales_team.group_sale_manager')
   ```
3. Test with manager and non-manager users in matching domain.

### Expected result
- Rule applies only when both domain and python condition are true.

## Scenario E — Runtime error handling
1. Set Python Condition to:
   ```python
   result = 1 / 0
   ```
2. Trigger approval check.

### Expected result
- User-friendly `UserError` is raised and explains there is an error in python condition.

## Regression checklist
- Approvals without Python Condition still work as before.
- Existing domain-only rules still behave unchanged.
- Notification order behavior remains intact.
