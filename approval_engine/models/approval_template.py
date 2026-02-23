from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class ApprovalTemplate(models.Model):
    _name = "approval.engine.template"
    _description = "Approval Template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, id"

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, tracking=True)

    approval_category_id = fields.Many2one(
        "approval.category",
        string="Approvals Form",
        tracking=True,
        help="Source form/category from the standard Approvals app.",
    )

    model_id = fields.Many2one(
        "ir.model",
        required=True,
        ondelete="cascade",
        domain="[(\"transient\", \"=\", False)]",
        tracking=True,
    )
    model = fields.Char(related="model_id.model", store=True, index=True)
    description = fields.Text()

    rule_type = fields.Selection(
        [
            ("always", "Always"),
            ("domain", "Domain"),
            ("python", "Python Expression"),
        ],
        default="always",
        required=True,
        tracking=True,
    )
    rule_domain = fields.Text(help="Domain expression, e.g. [('amount_total', '>', 10000)]")
    rule_python = fields.Text(help="Python expression returning True/False. Variables: record, user, env")

    on_approved_method = fields.Char(help="Method called on target record after final approval. Example: action_confirm")
    on_rejected_method = fields.Char(help="Method called on target record after rejection. Example: action_cancel")

    step_ids = fields.One2many("approval.engine.step", "template_id", copy=True)
    binding_ids = fields.One2many("approval.engine.binding", "template_id", string="UI Bindings", copy=True)

    _sql_constraints = [
        (
            "template_name_model_company_uniq",
            "unique(name, model_id, company_id)",
            "Template name must be unique per model and company.",
        ),
    ]

    @api.model
    def action_sync_from_approvals(self):
        """Create inactive engine templates from existing approvals categories."""
        categories = self.env["approval.category"].search([])
        created = 0
        for category in categories:
            exists = self.search([("approval_category_id", "=", category.id)], limit=1)
            if exists:
                continue

            self.create(
                {
                    "name": f"{category.name} [{category.id}]",
                    "approval_category_id": category.id,
                    "model_id": self.env.ref("base.model_res_partner").id,
                    "active": False,
                    "description": _("Imported from Approvals category. Select your target model and steps."),
                }
            )
            created += 1
        return created

    @api.constrains("rule_type", "rule_domain", "rule_python")
    def _check_rule_definition(self):
        for template in self:
            if template.rule_type == "domain" and not template.rule_domain:
                raise ValidationError(_("Rule domain is required when rule type is Domain."))
            if template.rule_type == "python" and not template.rule_python:
                raise ValidationError(_("Python expression is required when rule type is Python."))

    @api.constrains("step_ids", "active")
    def _check_steps(self):
        for template in self:
            if template.active and not template.step_ids:
                raise ValidationError(_("Active templates need at least one approval step."))

    @api.constrains("on_approved_method", "on_rejected_method")
    def _check_hook_names(self):
        for template in self:
            for method_name in [template.on_approved_method, template.on_rejected_method]:
                if method_name and not method_name.isidentifier():
                    raise ValidationError(_("Hook method names must be valid python identifiers."))

    def _rule_is_matching(self, record):
        self.ensure_one()
        if self.rule_type == "always":
            return True
        if self.rule_type == "domain":
            domain = safe_eval(self.rule_domain or "[]")
            return bool(record.search_count([("id", "=", record.id)] + domain))

        localdict = {"record": record, "user": self.env.user, "env": self.env}
        return bool(safe_eval(self.rule_python or "False", localdict))

    def _get_ordered_steps(self):
        self.ensure_one()
        return self.step_ids.sorted(key=lambda s: (s.sequence, s.id))


class ApprovalStep(models.Model):
    _name = "approval.engine.step"
    _description = "Approval Step"
    _order = "sequence, id"

    name = fields.Char(required=True)
    template_id = fields.Many2one("approval.engine.template", required=True, ondelete="cascade")
    sequence = fields.Integer(default=10)
    approver_group_id = fields.Many2one("res.groups", required=True)
    min_approvals = fields.Integer(default=1)
    require_all_group_users = fields.Boolean(
        string="Require All Group Users",
        help="If enabled, all users in the selected group must approve this step.",
    )

    @api.constrains("min_approvals")
    def _check_min_approvals(self):
        for step in self:
            if step.min_approvals < 1:
                raise ValidationError(_("Minimum approvals must be at least 1."))


class ApprovalBinding(models.Model):
    _name = "approval.engine.binding"
    _description = "Approval UI Binding"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    template_id = fields.Many2one("approval.engine.template", required=True, ondelete="cascade")
    model_id = fields.Many2one(related="template_id.model_id", store=True)
    model = fields.Char(related="template_id.model", store=True)

    view_id = fields.Many2one(
        "ir.ui.view",
        required=True,
        ondelete="cascade",
        domain="[(\"model\", \"=\", model), (\"type\", \"in\", [\"form\", \"list\", \"kanban\", \"activity\"]) ]",
        help="Select the target view where this approval entry point should be shown.",
    )
    trigger_method = fields.Char(
        required=True,
        help="Business model method that should trigger submission (example: action_submit_for_approval).",
    )
    button_label = fields.Char(default="Submit for Approval")

    @api.constrains("trigger_method")
    def _check_trigger_method(self):
        for rec in self:
            if rec.trigger_method and not rec.trigger_method.isidentifier():
                raise ValidationError(_("Trigger method must be a valid python identifier."))
