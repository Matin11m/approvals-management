from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ApprovalEngineMixin(models.AbstractModel):
    _name = "approval.engine.mixin"
    _description = "Approval Engine Integration Mixin"

    approval_request_count = fields.Integer(compute="_compute_approval_request_count")

    def _compute_approval_request_count(self):
        request_model = self.env["approval.engine.request"]
        for record in self:
            record.approval_request_count = request_model.search_count(
                [
                    ("res_model", "=", record._name),
                    ("res_id", "=", record.id),
                ]
            )

    def action_submit_for_approval(self):
        self.ensure_one()
        template = self._get_matching_template()
        if not template:
            raise UserError(_("No matching active approval template found for this record."))

        request = self.env["approval.engine.request"].create(
            {
                "template_id": template.id,
                "company_id": self.company_id.id if "company_id" in self else self.env.company.id,
                "res_model": self._name,
                "res_id": self.id,
            }
        )
        request.action_submit()
        return request

    @api.model
    def _get_matching_template(self):
        self.ensure_one()
        templates = self.env["approval.engine.template"].search(
            [
                ("active", "=", True),
                ("model", "=", self._name),
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.company_id.id if "company_id" in self else self.env.company.id),
            ],
            order="sequence, id",
        )
        for template in templates:
            if template._rule_is_matching(self):
                return template
        return False

    def action_view_approval_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Approval Requests"),
            "res_model": "approval.engine.request",
            "view_mode": "list,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"default_res_model": self._name, "default_res_id": self.id},
        }
