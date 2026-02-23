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
