# Approval Engine (Odoo 19)

A generic, model-driven approval app.

## Highlights
- Configurable templates per model (`ir.model` based).
- Multi-step approvals with group-based approvers.
- Rule execution with Domain or Python expression.
- Generic request lifecycle: draft → waiting → approved/rejected/cancelled.
- Optional record hooks (`on_approved_method`, `on_rejected_method`).
- Audit logs per step/user.

## Integrating on a business model
Inherit `approval.engine.mixin` on your model and call:
- `action_submit_for_approval()`
- `action_view_approval_requests()`

Example:
```python
class PurchaseOrder(models.Model):
    _inherit = ["purchase.order", "approval.engine.mixin"]
```

Then add a button in the form view to submit for approval.


## Where to find it in Odoo
1. Go to **Apps** and install **Approval Engine**.
2. Open the app launcher (home screen): you will see **Approval Engine**.
3. Inside the app:
   - **Requests**: operational approval requests.
   - **Templates** (manager): configure model-based approval flows.

## Basic setup
1. Open **Approval Engine > Templates**.
2. Create a template and select target **Model** (e.g. `purchase.order`).
3. Add one or more **Steps** with approver group and rule.
4. (Optional) set `on_approved_method` / `on_rejected_method` to call business methods.
