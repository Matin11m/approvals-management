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
    rule_domain = fields.Text(
        help="Domain expression, e.g. [('amount_total', '>', 10000)]"
    )
    rule_python = fields.Text(
        help="Python expression returning True/False. Variables: record, user, env"
    )
    on_approved_method = fields.Char(
        help="Method called on target record after final approval. Example: action_confirm"
    )
    on_rejected_method = fields.Char(
        help="Method called on target record after rejection. Example: action_cancel"
    )
    step_ids = fields.One2many("approval.engine.step", "template_id", copy=True)

    _sql_constraints = [
        ("template_name_model_company_uniq", "unique(name, model_id, company_id)", "Template name must be unique per model and company."),
    ]

    @api.constrains("rule_type", "rule_domain", "rule_python")
    def _check_rule_definition(self):
        for template in self:
            if template.rule_type == "domain" and not template.rule_domain:
                raise ValidationError(_("Rule domain is required when rule type is Domain."))
            if template.rule_type == "python" and not template.rule_python:
                raise ValidationError(_("Python expression is required when rule type is Python."))

    @api.constrains("step_ids")
    def _check_steps(self):
        for template in self:
            if not template.step_ids:
                raise ValidationError(_("Each template needs at least one approval step."))

    def _rule_is_matching(self, record):
        self.ensure_one()
        if self.rule_type == "always":
            return True
        if self.rule_type == "domain":
            domain = safe_eval(self.rule_domain or "[]")
            return bool(record.search_count([("id", "=", record.id)] + domain))

        # python rule
        localdict = {
            "record": record,
            "user": self.env.user,
            "env": self.env,
        }
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
