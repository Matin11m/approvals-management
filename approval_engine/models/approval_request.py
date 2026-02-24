from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ApprovalRequest(models.Model):
    _name = "approval.engine.request"
    _description = "Approval Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "id desc"

    name = fields.Char(default=lambda self: _("New"), copy=False)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, index=True)
    template_id = fields.Many2one("approval.engine.template", required=True, index=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("waiting", "Waiting Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    res_model = fields.Char(required=True, index=True)
    res_id = fields.Integer(required=True, index=True)
    reference = fields.Reference(selection="_referenceable_models", compute="_compute_reference", store=False)
    requester_id = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
    current_step_id = fields.Many2one("approval.engine.step", tracking=True)
    log_ids = fields.One2many("approval.engine.log", "request_id")

    python_rule_mode = fields.Selection(
        [
            ("none", "Disabled"),
            ("manual", "Manual Only"),
            ("approve", "On Approve"),
            ("reject", "On Reject"),
            ("both", "On Approve and Reject"),
        ],
        default="none",
        string="Python Rule Mode",
        tracking=True,
    )
    python_rule_code = fields.Text(
        string="Python Execute Code",
        help=(
            "Python code executed with safe_eval(mode='exec').\n"
            "Available variables: request, record, env, user, action.\n"
            "Set variable `result` to True/False to allow/block the action.\n"
            "Optional: set `message` for a user-facing error."
        ),
        tracking=True,
    )
    python_last_result = fields.Char(readonly=True)
    python_last_log = fields.Text(readonly=True)

    @api.constrains("state", "template_id", "res_model", "res_id")
    def _check_single_open_request(self):
        for request in self:
            if request.state not in ("draft", "waiting"):
                continue
            count = self.search_count(
                [
                    ("id", "!=", request.id),
                    ("template_id", "=", request.template_id.id),
                    ("res_model", "=", request.res_model),
                    ("res_id", "=", request.res_id),
                    ("state", "in", ["draft", "waiting"]),
                ]
            )
            if count:
                raise UserError(_("There is already an open approval request for this record and template."))

    @api.model
    def _referenceable_models(self):
        models = self.env["ir.model"].search([("transient", "=", False)])
        return [(m.model, m.name) for m in models]

    @api.depends("res_model", "res_id")
    def _compute_reference(self):
        for request in self:
            request.reference = "%s,%s" % (request.res_model, request.res_id) if request.res_model and request.res_id else False

    @api.model_create_multi
    def create(self, vals_list):
        seq = self.env["ir.sequence"]
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = seq.next_by_code("approval.engine.request") or _("New")
        return super().create(vals_list)

    def _get_target_record(self):
        self.ensure_one()
        return self.env[self.res_model].browse(self.res_id).exists()

    def _is_python_rule_enabled_for(self, action):
        self.ensure_one()
        return self.python_rule_mode in {"both", action}

    def _execute_python_rule(self, action):
        self.ensure_one()
        if not self.python_rule_code or not self._is_python_rule_enabled_for(action):
            return True

        record = self._get_target_record()
        localdict = {
            "request": self,
            "record": record,
            "env": self.env,
            "user": self.env.user,
            "action": action,
            "result": True,
            "message": "",
        }
        try:
            safe_eval(self.python_rule_code, localdict, mode="exec", nocopy=True)
        except Exception as exc:
            self.write({"python_last_result": "error", "python_last_log": str(exc)})
            raise UserError(_("Python rule execution failed: %s") % str(exc))

        allow = bool(localdict.get("result", True))
        msg = localdict.get("message") or ""
        self.write({"python_last_result": "allowed" if allow else "blocked", "python_last_log": msg})
        if not allow:
            raise UserError(msg or _("Action blocked by custom Python rule."))
        return True

    def action_execute_custom_python_rule(self):
        for request in self:
            request._execute_python_rule("manual")

    def action_submit(self):
        for request in self:
            if request.state not in ("draft", "cancelled"):
                continue
            steps = request.template_id._get_ordered_steps()
            if not steps:
                raise UserError(_("Template has no steps."))
            request.write({"state": "waiting", "current_step_id": steps[0].id})
            request.message_post(body=_("Request submitted for approval."))

    def _check_user_can_approve_step(self, step):
        self.ensure_one()
        user = self.env.user
        if user not in step.approver_group_id.users:
            raise UserError(_("You are not allowed to approve this step."))

    def action_approve(self, comment=None):
        for request in self:
            request._execute_python_rule("approve")
            if request.state != "waiting":
                raise UserError(_("Only waiting requests can be approved."))
            step = request.current_step_id
            if not step:
                raise UserError(_("There is no active step to approve."))

            request._check_user_can_approve_step(step)
            if request.log_ids.filtered(lambda l: l.step_id == step and l.user_id == self.env.user and l.action == "approved"):
                raise UserError(_("You already approved this step."))

            self.env["approval.engine.log"].create(
                {
                    "request_id": request.id,
                    "step_id": step.id,
                    "user_id": self.env.user.id,
                    "action": "approved",
                    "comment": comment,
                }
            )

            if request._is_step_completed(step):
                request._move_to_next_step_or_finish()

    def _is_step_completed(self, step):
        self.ensure_one()
        approved_logs = self.log_ids.filtered(lambda l: l.step_id == step and l.action == "approved")
        if step.require_all_group_users:
            return set(approved_logs.user_id.ids) >= set(step.approver_group_id.users.ids)
        return len(approved_logs) >= step.min_approvals

    def _move_to_next_step_or_finish(self):
        self.ensure_one()
        steps = self.template_id._get_ordered_steps()
        current_index = steps.ids.index(self.current_step_id.id)
        if current_index + 1 < len(steps):
            self.write({"current_step_id": steps[current_index + 1].id})
            return

        self.write({"state": "approved", "current_step_id": False})
        self.message_post(body=_("Request fully approved."))
        self._run_record_hook("approved")

    def action_reject(self, reason=None):
        for request in self:
            request._execute_python_rule("reject")
            if request.state != "waiting":
                raise UserError(_("Only waiting requests can be rejected."))
            step = request.current_step_id
            request._check_user_can_approve_step(step)
            self.env["approval.engine.log"].create(
                {
                    "request_id": request.id,
                    "step_id": step.id,
                    "user_id": self.env.user.id,
                    "action": "rejected",
                    "comment": reason,
                }
            )
            request.write({"state": "rejected", "current_step_id": False})
            request.message_post(body=_("Request rejected."))
            request._run_record_hook("rejected")

    def action_cancel(self):
        self.write({"state": "cancelled", "current_step_id": False})

    def _run_record_hook(self, result):
        self.ensure_one()
        target = self._get_target_record()
        if not target:
            return

        method_name = self.template_id.on_approved_method if result == "approved" else self.template_id.on_rejected_method
        if method_name and hasattr(target, method_name):
            getattr(target, method_name)()


class ApprovalLog(models.Model):
    _name = "approval.engine.log"
    _description = "Approval Decision Log"
    _order = "create_date desc, id desc"

    request_id = fields.Many2one("approval.engine.request", required=True, ondelete="cascade")
    step_id = fields.Many2one("approval.engine.step", required=True)
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    action = fields.Selection(
        [
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        required=True,
    )
    comment = fields.Text()
