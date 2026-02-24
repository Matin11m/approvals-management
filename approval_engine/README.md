# Approval Engine (Odoo 19)

A generic, model-driven approval app.

## What this structure provides
1. **Import forms from Approvals app** (`approval.category`) into Approval Engine templates.
2. **Attach each template to any Odoo model** (`ir.model`).
3. **Select target views of that model** and define which method/function should trigger approval.
4. Keep custom rule design extensible (Domain/Python) for future phases.

## Highlights
- Configurable templates per model (`ir.model` based).
- Optional link to source Approvals form/category.
- Multi-step approvals with group-based approvers.
- Rule execution with Domain or Python expression.
- Generic request lifecycle: draft → waiting → approved/rejected/cancelled.
- Optional record hooks (`on_approved_method`, `on_rejected_method`).
- UI Binding section to select model views (`ir.ui.view`) + trigger method.
- Audit logs per step/user.

## Where to find it in Odoo
1. Go to **Apps** and install **Approval Engine**.
2. Open app launcher: **Approval Engine**.
3. In app menus:
   - **Approvals Forms**: existing forms from Approvals module.
   - **Templates**: map form -> model -> views/functions.
   - **Requests**: operational approvals.

## Basic setup flow
1. Open **Approval Engine > Templates**.
2. Pick **Approvals Form** (imported from `approval.category`).
3. Choose target **Model** (any business model).
4. Add **UI Bindings** lines:
   - target `view_id`
   - `trigger_method`
   - optional button label
5. Add approval **Steps** and activate template.

## Integration on a business model
Inherit `approval.engine.mixin` on your model and call:
- `action_submit_for_approval()`
- `action_view_approval_requests()`

Example:
```python
class PurchaseOrder(models.Model):
    _inherit = ["purchase.order", "approval.engine.mixin"]
```


## Documentation
- Test scenarios (FA): `approval_engine/docs/approval_engine_test_scenarios_fa.md`
- Full manual (FA): `approval_engine/docs/approval_engine_full_manual_fa.md`
- Technical spec (FA): `approval_engine/docs/approval_engine_technical_spec_fa.md`
- User guide (FA): `approval_engine/docs/approval_engine_user_guide_fa.md`


## Current Access-Control Policy
At this stage, fine-grained ACL/groups are intentionally postponed.
A temporary flat access policy is enabled for internal users (`base.group_user`) so core menus (Requests/Templates) are visible and usable.
Define strict role-based policies in a later hardening phase.
