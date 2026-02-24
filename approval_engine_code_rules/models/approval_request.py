from odoo import fields, models, _
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval


class ApprovalEngineRequest(models.Model):
    _inherit = "approval.engine.request"

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

    def _is_python_rule_enabled_for(self, action):
        self.ensure_one()
        return self.python_rule_mode in {
            "both",
            action,
        }

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
            self.write(
                {
                    "python_last_result": "error",
                    "python_last_log": str(exc),
                }
            )
            raise UserError(_("Python rule execution failed: %s") % str(exc))

        allow = bool(localdict.get("result", True))
        msg = localdict.get("message") or ""
        self.write(
            {
                "python_last_result": "allowed" if allow else "blocked",
                "python_last_log": msg,
            }
        )
        if not allow:
            raise UserError(msg or _("Action blocked by custom Python rule."))
        return True

    def action_execute_custom_python_rule(self):
        for request in self:
            request._execute_python_rule("manual")

    def action_approve(self, comment=None):
        for request in self:
            request._execute_python_rule("approve")
        return super().action_approve(comment=comment)

    def action_reject(self, reason=None):
        for request in self:
            request._execute_python_rule("reject")
        return super().action_reject(reason=reason)
