from ast import literal_eval, parse
from collections import defaultdict
import logging

from odoo import api, fields, models, _
from odoo.fields import Domain
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


class StudioApprovalRule(models.Model):
    _inherit = "studio.approval.rule"

    _APPROVER_PYTHON_CODE_GUIDE = _(
        """Approver Python Guide
Available variables:
- env: Odoo environment
- user: current user
- record: current business record
- rule: current approval rule
- result: users output

Allowed result types:
- res.users recordset
- single user id (int)
- list/tuple/set of user ids

Examples:
- result = record.user_id
- result = [env.user.id]
- result = record.team_id.user_id"""
    )

    _NOTIFY_PYTHON_CODE_GUIDE = _(
        """Notify Python Guide
Available variables:
- env: Odoo environment
- user: current user
- record: current business record
- rule: current approval rule
- result: users output

Allowed result types:
- res.users recordset
- single user id (int)
- list/tuple/set of user ids

Examples:
- result = record.team_id.member_ids
- result = [record.user_id.id]
- result = env.user"""
    )

    python_code = fields.Text(
        string="Approver Python Condition",
        help="Optional python code to decide if this rule applies for approvers. Set a boolean on `result` (default is True). Available variables: env, user, record, rule.",
    )
    notify_python_code = fields.Text(
        string="Notify Approver Python Condition",
        help="Optional python code to decide if approvers should be notified. Set a boolean on `result` (default is True). Available variables: env, user, record, rule.",
    )
    approver_python_code_guide = fields.Text(
        string="Approver Python Guide",
        compute="_compute_python_code_guides",
        readonly=True,
    )
    notify_python_code_guide = fields.Text(
        string="Notify Python Guide",
        compute="_compute_python_code_guides",
        readonly=True,
    )

    def _compute_python_code_guides(self):
        for rule in self:
            rule.approver_python_code_guide = self._APPROVER_PYTHON_CODE_GUIDE
            rule.notify_python_code_guide = self._NOTIFY_PYTHON_CODE_GUIDE

    @api.depends("domain", "python_code", "notify_python_code")
    def _compute_conditional(self):
        for rule in self:
            rule.conditional = bool(rule.domain or rule.python_code or rule.notify_python_code)

    @api.constrains("python_code", "notify_python_code")
    def _check_python_code(self):
        for rule in self:
            for field_name in ("python_code", "notify_python_code"):
                code = rule[field_name]
                if not code:
                    continue
                try:
                    parse(code)
                except SyntaxError as error:
                    raise ValidationError(_("Invalid python condition syntax in %s: %s", field_name, error))

    def _is_rule_applicable(self, record, domain=None, python_code=None):
        self.ensure_one()
        parsed_domain = literal_eval(domain or "[]")
        if parsed_domain and not record.filtered_domain(parsed_domain):
            return False
        if not python_code:
            return True

        localdict = {
            "env": self.env,
            "user": self.env.user,
            "record": record,
            "rule": self,
            "result": True,
        }
        try:
            safe_eval(python_code, localdict, mode="exec", nocopy=True)
        except Exception as error:
            _logger.exception("Error while evaluating python condition for approval rule %s", self.id)
            raise UserError(_("Error in python condition for rule '%(rule)s': %(error)s", rule=self.display_name, error=error))
        return bool(localdict.get("result"))

    def _extract_user_ids(self, value):
        if not value:
            return []
        if isinstance(value, models.Model):
            if value._name != "res.users":
                raise UserError(_("Python code result must be res.users, ids list, or id."))
            return value.ids
        if isinstance(value, int):
            return [value]
        if isinstance(value, (list, tuple, set)):
            user_ids = []
            for item in value:
                if isinstance(item, int):
                    user_ids.append(item)
                elif isinstance(item, models.Model) and item._name == "res.users":
                    user_ids.extend(item.ids)
                else:
                    raise UserError(_("Python code result list must contain user ids or res.users records."))
            return user_ids
        raise UserError(_("Python code result must be res.users, ids list, or id."))

    def _eval_user_python_code(self, record, code, field_label):
        self.ensure_one()
        if not code:
            return self.env["res.users"]
        localdict = {
            "env": self.env,
            "user": self.env.user,
            "record": record,
            "rule": self,
            "result": [],
        }
        try:
            safe_eval(code, localdict, mode="exec", nocopy=True)
        except Exception as error:
            _logger.exception("Error while evaluating %s for approval rule %s", field_label, self.id)
            raise UserError(_("Error in %(field)s for rule '%(rule)s': %(error)s", field=field_label, rule=self.display_name, error=error))

        user_ids = self._extract_user_ids(localdict.get("result"))
        if not user_ids:
            return self.env["res.users"]
        return self.env["res.users"].browse(user_ids).exists()

    def _get_rule_approvers(self, record):
        self.ensure_one()
        if self.python_code:
            return self._eval_user_python_code(record, self.python_code, _("Approver Python Condition"))
        return self.approver_ids

    def _get_rule_notify_users(self, record):
        self.ensure_one()
        if self.notify_python_code:
            return self._eval_user_python_code(record, self.notify_python_code, _("Notify Approver Python Condition"))
        return self.users_to_notify

    def delete_approval(self, res_id):
        self.ensure_one()
        record = self.env[self.sudo().model_name].browse(res_id)
        record.check_access('write')
        rule_sudo = self.sudo()

        existing_entry = self.env['studio.approval.entry'].sudo().search([
            ('model', '=', rule_sudo.model_name),
            ('method', '=', rule_sudo.method), ('action_id', '=', rule_sudo.action_id.id),
            ('res_id', '=', res_id), ('rule_id', '=', self.id)
        ])
        if existing_entry and existing_entry.user_id != self.env.user:
            rules_above = self.env["studio.approval.rule"].sudo().search_read([
                ('model_name', '=', rule_sudo.model_name),
                ('method', '=', rule_sudo.method), ('action_id', '=', rule_sudo.action_id.id),
                ('notification_order', ">", rule_sudo.notification_order)
            ], ["domain", "python_code", "notify_python_code", "can_validate"], order="notification_order DESC")

            can_revoke = False
            for rule in rules_above:
                if not self.browse(rule["id"])._is_rule_applicable(record, rule.get("domain"), rule.get("python_code")):
                    continue
                if rule["can_validate"]:
                    can_revoke = True
                    break

            if not can_revoke:
                raise UserError(_("You cannot cancel an approval you didn't set yourself or you don't belong to an higher level rule's approvers."))
        if not existing_entry:
            raise UserError(_("No approval found for this rule, record and user combination."))
        return existing_entry.unlink()

    def _set_approval(self, res_id, approved):
        self.ensure_one()
        self = self._clean_context()
        rule_sudo = self.sudo()
        domain = self._get_rule_domain(rule_sudo.model_name, rule_sudo.method, rule_sudo.action_id)
        all_rule_ids = tuple(rule_sudo.search(domain).ids)
        if not all_rule_ids:
            return None
        self.env.cr.execute('SELECT id FROM studio_approval_rule WHERE id IN %s FOR UPDATE NOWAIT', (all_rule_ids,))
        record = self.env[self.sudo().model_name].browse(res_id)
        record.check_access('write')
        if not rule_sudo.can_validate:
            raise UserError(_('You can not approve this rule.'))

        existing_entry = rule_sudo.env['studio.approval.entry'].search([
            ('rule_id', '=', self.id), ('res_id', '=', res_id)
        ])
        if existing_entry:
            raise UserError(_('This rule has already been approved/rejected.'))

        other_entries = rule_sudo.env['studio.approval.entry'].search([
            ('rule_id', 'in', all_rule_ids), ('res_id', '=', res_id)
        ])
        if other_entries:
            existing_rule_ids = other_entries.mapped('rule_id').ids
            rule_limitation_msg = _('You can not approve this rule because another rule has already been approved/rejected.')
            if rule_sudo.exclusive_user:
                if any(other_entries.filtered(lambda e: e.user_id == self.env.user)):
                    raise UserError(rule_limitation_msg)
            else:
                rules_with_exclusive = rule_sudo.browse(existing_rule_ids).filtered('exclusive_user')
                if any(rules_with_exclusive.filtered(lambda r: r.can_validate)):
                    raise UserError(rule_limitation_msg)

        result = rule_sudo.env['studio.approval.entry'].create({
            'user_id': self.env.uid,
            'rule_id': rule_sudo.id,
            'res_id': res_id,
            'approved': approved,
        })
        if not self.env.context.get('prevent_approval_request_unlink'):
            rule_sudo._unlink_request(res_id)

        if approved and rule_sudo.notification_order != '9':
            same_level_rules = []
            higher_level_rules = []
            for rule in rule_sudo.search_read([
                ('notification_order', '>=', rule_sudo.notification_order),
                ('active', '=', True),
                ("model_name", "=", rule_sudo.model_name),
                ('method', '=', rule_sudo.method),
                ('action_id', '=', rule_sudo.action_id.id)
            ], ["domain", "python_code", "notify_python_code", "notification_order"]):
                if rule["id"] == rule_sudo.id:
                    continue
                if not self.browse(rule["id"])._is_rule_applicable(record, rule.get("domain"), rule.get("python_code")):
                    continue
                if rule["notification_order"] == rule_sudo.notification_order:
                    same_level_rules.append(rule["id"])
                else:
                    higher_level_rules.append(rule["id"])

            should_notify_higher = not same_level_rules
            if same_level_rules:
                approved_entries = rule_sudo.env["studio.approval.entry"].search_read([
                    ("rule_id", "in", same_level_rules), ("res_id", "=", record.id), ("approved", "=", True)
                ], ["rule_id"])
                if approved_entries:
                    entry_rule_ids = {entry["rule_id"][0] for entry in approved_entries}
                    should_notify_higher = all(same_level_id in entry_rule_ids for same_level_id in same_level_rules)
                else:
                    should_notify_higher = False
            if should_notify_higher:
                for rule in rule_sudo.browse(higher_level_rules):
                    rule._create_request(res_id)
        return result

    @api.model
    def _get_approval_spec(self, model, spec):
        records = self.env[model]
        records.check_access('read')

        def m2o_to_id(t_uple):
            return t_uple and t_uple[0]

        all_res_ids = set()
        all_methods = set()
        all_action_ids = set()
        for (method, action_id), ids in spec.items():
            all_res_ids |= ids
            if method:
                all_methods.add(method)
            if action_id:
                all_action_ids.add(action_id)
        res_ids = [_id for _id in all_res_ids if _id]
        if res_ids:
            records = records.browse(res_ids).exists()
            records.check_access('read')

        rules_domain = Domain('model_name', '=', model) & (
            Domain("method", "in", list(all_methods))
            | Domain("action_id", "in", list(all_action_ids))
        )
        rules_data = self.sudo().search_read(
            domain=rules_domain,
            fields=['name', 'message', 'exclusive_user', 'can_validate', 'action_id', 'method', "approver_ids", "users_to_notify", "approval_group_id", "notification_order", "domain", "python_code", "notify_python_code"],
            order='notification_order asc, exclusive_user desc, id asc')

        results = defaultdict(dict)
        res_ids_for_entries = set()
        rule_ids_for_entries = set()
        map_rules = {}
        for rule in rules_data:
            map_rules[rule["id"]] = rule
            res_ids_for_rule = spec[(rule["method"], m2o_to_id(rule["action_id"]))]
            records_for_rule = records.browse([_id for _id in res_ids_for_rule if _id]).with_prefetch(records.ids or None)
            rule_domain_str = rule.get('domain')
            rule_domain = rule_domain_str and literal_eval(rule_domain_str)
            rule['domain'] = rule_domain or False

            record_ids_for_result = []
            if records_for_rule:
                record_ids_for_result = [
                    rec.id
                    for rec in records_for_rule
                    if self.browse(rule['id'])._is_rule_applicable(rec, rule_domain_str, rule.get('python_code'))
                ]

            if record_ids_for_result:
                rule_ids_for_entries.add(rule["id"])

            if False in res_ids_for_rule:
                res_ids_for_entries.add(False)
                key = (False, rule["method"], m2o_to_id(rule["action_id"]))
                results[key].setdefault("rules", []).append(rule)
                results[key].setdefault("entries", [])
            for record_id in record_ids_for_result:
                res_ids_for_entries.add(record_id)
                key = (record_id, rule["method"], m2o_to_id(rule["action_id"]))
                record = records_for_rule.browse(record_id)
                rule_data = dict(rule)
                rule_data["approver_ids"] = self.browse(rule["id"])._get_rule_approvers(record).ids
                rule_data["users_to_notify"] = self.browse(rule["id"])._get_rule_notify_users(record).ids
                results[key].setdefault("rules", []).append(rule_data)
                results[key].setdefault("entries", [])

        entries_data = self.env['studio.approval.entry'].sudo().search_read(
            domain=[('model', '=', model), ('res_id', 'in', list(res_ids_for_entries)), ('rule_id', 'in', list(rule_ids_for_entries))],
            fields=['approved', 'user_id', 'write_date', 'rule_id', 'model', 'res_id'])

        for entry in entries_data:
            rule = map_rules[entry["rule_id"][0]]
            key = (entry["res_id"], rule["method"], m2o_to_id(rule["action_id"]))
            results[key]["entries"].append(entry)

        return model, map_rules, results

    @api.model
    def check_approval(self, model, res_id, method, action_id):
        self = self._clean_context()
        if method and action_id:
            raise UserError(_('Approvals can only be done on a method or an action, not both.'))
        record = self.env[model].browse(res_id)
        record.check_access('write')
        rule_sudo = self.sudo()
        domain = self._get_rule_domain(model, method, action_id)
        rules_data = rule_sudo.search_read(
            domain=domain,
            fields=['message', 'name', 'domain', 'python_code', 'notify_python_code'],
            order='notification_order asc, exclusive_user desc, id asc'
        )
        applicable_rule_ids = []
        for rule in rules_data:
            if self.browse(rule['id'])._is_rule_applicable(record, rule.get('domain'), rule.get('python_code')):
                applicable_rule_ids.append(rule['id'])
        rules_data = list(filter(lambda r: r['id'] in applicable_rule_ids, rules_data))
        if not rules_data:
            return {'approved': True, 'rules': [], 'entries': []}

        entries_data = self.env['studio.approval.entry'].sudo().search_read(
            domain=[('model', '=', model), ('res_id', '=', res_id), ('rule_id', 'in', applicable_rule_ids)],
            fields=['approved', 'rule_id', 'user_id'])
        entries_by_rule = dict.fromkeys(applicable_rule_ids, False)
        for rule_id in entries_by_rule:
            candidate_entry = list(filter(lambda e: e['rule_id'][0] == rule_id, entries_data))
            candidate_entry = candidate_entry and candidate_entry[0]
            if not candidate_entry:
                try:
                    new_entry = self.browse(rule_id)._set_approval(res_id, True)
                    entries_data.append({
                        'id': new_entry.id,
                        'approved': True,
                        'rule_id': [rule_id, False],
                        'user_id': (self.env.user.id, self.env.user.display_name),
                    })
                    entries_by_rule[rule_id] = True
                except UserError:
                    self.browse(rule_id)._create_request(res_id)
                    pass
            else:
                entries_by_rule[rule_id] = candidate_entry['approved']
        return {
            'approved': all(entries_by_rule.values()),
            'rules': rules_data,
            'entries': entries_data,
        }

    def _create_request(self, res_id):
        self.ensure_one()
        rule_sudo = self.sudo()
        if not self.model_id.sudo().is_mail_activity:
            return False

        record = self.env[rule_sudo.model_name].browse(res_id)
        users = rule_sudo._get_rule_approvers(record)
        if not users:
            return False

        requests = self.env['studio.approval.request'].sudo().search([('rule_id', '=', self.id), ('res_id', '=', res_id)])
        if requests:
            return False
        if self.notification_order != '1':
            entry_sudo = self.env["studio.approval.entry"].sudo()
            for approval_rule in rule_sudo.search([
                ('notification_order', '<', self.notification_order),
                ('active', '=', True),
                ("model_name", "=", rule_sudo.model_name),
                ('method', '=', rule_sudo.method),
                ('action_id', '=', rule_sudo.action_id.id)
            ]):
                if not approval_rule._is_rule_applicable(record, approval_rule.domain, approval_rule.python_code):
                    continue
                existing_entry = entry_sudo.search([
                    ('model', '=', rule_sudo.model_name),
                    ('method', '=', rule_sudo.method),
                    ('action_id', '=', rule_sudo.action_id.id),
                    ('res_id', '=', res_id),
                    ('rule_id', '=', approval_rule.id)
                ])
                if not existing_entry or not existing_entry.approved:
                    return False

        return super()._create_request(res_id)


class StudioApprovalEntry(models.Model):
    _inherit = "studio.approval.entry"

    def _notify_approval(self):
        for entry in self:
            if not entry.rule_id.model_id.is_mail_thread:
                continue
            record = self.env[entry.model].browse(entry.res_id)
            notify_users = entry.rule_id._get_rule_notify_users(record)
            partner_ids = notify_users.partner_id
            rule = entry.rule_id
            target_name = ""
            if rule.name:
                target_name = rule.name
            elif rule.method:
                target_name = _("Method: %s", rule.method)
            elif rule.action_id.name:
                target_name = _("Action: %s", rule.action_id.name)

            record.message_post_with_source(
                'web_studio.notify_approval',
                author_id=entry.user_id.partner_id.id,
                partner_ids=partner_ids.ids,
                render_values={
                    'partner_ids': partner_ids,
                    'target_name': target_name,
                    'approved': entry.approved,
                    'user': entry.user_id,
                },
                subtype_xmlid='mail.mt_note',
            )
