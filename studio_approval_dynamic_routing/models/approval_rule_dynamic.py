from ast import literal_eval, parse
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class StudioApprovalRuleDynamic(models.Model):
    _inherit = "studio.approval.rule"

    _APPROVER_GUIDE_MAIN = _(
        """Approver Python Guide
Variables:
- env
- user
- record
- rule
- result

Allowed result:
- res.users recordset
- user id (int)
- list/tuple/set of user ids"""
    )
    _APPROVER_GUIDE_EXAMPLES = _(
        """Approver Examples
- result = record.user_id
- result = [env.user.id]
- result = record.team_id.user_id"""
    )
    _NOTIFY_GUIDE_MAIN = _(
        """Notify Python Guide
Variables:
- env
- user
- record
- rule
- result

Allowed result:
- res.users recordset
- user id (int)
- list/tuple/set of user ids"""
    )
    _NOTIFY_GUIDE_EXAMPLES = _(
        """Notify Examples
- result = record.team_id.member_ids
- result = [record.user_id.id]
- result = env.user"""
    )

    python_code = fields.Text(
        string="Approver Python Condition",
        help="Optional python code to define approvers. Assign users to `result`.",
    )
    notify_python_code = fields.Text(
        string="Notify Approver Python Condition",
        help="Optional python code to define notify users. Assign users to `result`.",
    )
    approver_python_code_guide = fields.Text(
        string="Approver Python Guide",
        compute="_compute_dynamic_guides",
        readonly=True,
    )
    approver_python_examples_guide = fields.Text(
        string="Approver Python Examples",
        compute="_compute_dynamic_guides",
        readonly=True,
    )
    notify_python_code_guide = fields.Text(
        string="Notify Python Guide",
        compute="_compute_dynamic_guides",
        readonly=True,
    )
    notify_python_examples_guide = fields.Text(
        string="Notify Python Examples",
        compute="_compute_dynamic_guides",
        readonly=True,
    )

    def _compute_dynamic_guides(self):
        for rule in self:
            rule.approver_python_code_guide = self._APPROVER_GUIDE_MAIN
            rule.approver_python_examples_guide = self._APPROVER_GUIDE_EXAMPLES
            rule.notify_python_code_guide = self._NOTIFY_GUIDE_MAIN
            rule.notify_python_examples_guide = self._NOTIFY_GUIDE_EXAMPLES

    @api.depends("domain", "python_code", "notify_python_code")
    def _compute_conditional(self):
        for rule in self:
            rule.conditional = bool(rule.domain or rule.python_code or rule.notify_python_code)

    @api.constrains("python_code", "notify_python_code")
    def _validate_dynamic_python(self):
        for rule in self:
            for field_name in ("python_code", "notify_python_code"):
                code = rule[field_name]
                if not code:
                    continue
                try:
                    parse(code)
                except SyntaxError as error:
                    raise ValidationError(_("Invalid python condition syntax in %s: %s", field_name, error))

    def _match_rule_with_python(self, record, domain=None, python_code=None):
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
            "UserError": UserError,
        }
        try:
            safe_eval(python_code, localdict, mode="exec")
        except Exception as error:
            _logger.exception("Error while evaluating python condition for approval rule %s", self.id)
            raise UserError(
                _("Error in python condition for rule '%(rule)s': %(error)s", rule=self.display_name, error=error))
        return bool(localdict.get("result"))

    def _normalize_dynamic_user_ids(self, value):
        if not value:
            return []
        if isinstance(value, models.Model):
            if value._name != "res.users":
                raise UserError(_("Python code result must be res.users, ids list, or id."))
            return value.ids
        if isinstance(value, bool):
            raise UserError(_("Python code result must be user id(s) or res.users; boolean is not allowed."))
        if isinstance(value, int):
            return [value]
        if isinstance(value, (list, tuple, set)):
            user_ids = []
            for item in value:
                if isinstance(item, bool):
                    raise UserError(_("Python code result list cannot contain boolean values."))
                if isinstance(item, int):
                    user_ids.append(item)
                elif isinstance(item, models.Model) and item._name == "res.users":
                    user_ids.extend(item.ids)
                else:
                    raise UserError(_("Python code result list must contain user ids or res.users records."))
            return user_ids
        raise UserError(_("Python code result must be res.users, ids list, or id."))

    def _eval_dynamic_users(self, record, code, field_label):
        self.ensure_one()
        if not code:
            return self.env["res.users"]
        localdict = {
            "env": self.env,
            "user": self.env.user,
            "record": record,
            "rule": self,
            "result": [],
            "UserError": UserError,
        }
        try:
            safe_eval(code, localdict, mode="exec")
        except Exception as error:
            _logger.exception("Error while evaluating %s for approval rule %s", field_label, self.id)
            raise UserError(
                _("Error in %(field)s for rule '%(rule)s': %(error)s", field=field_label, rule=self.display_name,
                  error=error))

        user_ids = self._normalize_dynamic_user_ids(localdict.get("result"))
        if not user_ids:
            return self.env["res.users"]
        return self.env["res.users"].browse(user_ids).exists()

    def _resolve_dynamic_approvers(self, record):
        self.ensure_one()
        if self.python_code:
            return self._eval_dynamic_users(record, self.python_code, _("Approver Python Condition"))
        return self.approver_ids

    def _resolve_dynamic_notify_users(self, record):
        self.ensure_one()
        if self.notify_python_code:
            return self._eval_dynamic_users(record, self.notify_python_code, _("Notify Approver Python Condition"))
        return self.users_to_notify

    def _get_dynamic_group_field(self):
        """Return group-approval field metadata when available on rule model."""
        self.ensure_one()
        preferred_names = ("approval_group_id", "approver_group_id", "group_id", "group_ids")
        fields_map = self._fields

        for field_name in preferred_names:
            field = fields_map.get(field_name)
            if field and getattr(field, "comodel_name", None) == "res.groups":
                return field_name, field

        for field_name, field in fields_map.items():
            if getattr(field, "comodel_name", None) != "res.groups":
                continue
            if field.type not in ("many2one", "many2many"):
                continue
            return field_name, field
        return None, None

    def _sync_dynamic_approvers_and_group(self, record):
        """Populate approver/group fields from python routing or raise explicit errors."""
        self.ensure_one()
        if not self.python_code:
            return self.approver_ids

        users = self._eval_dynamic_users(record, self.python_code, _("Approver Python Condition"))
        if not users:
            raise UserError(_("Approver Python code did not resolve any users."))

        self.write({"approver_ids": [(6, 0, users.ids)]})

        group_field_name, group_field = self._get_dynamic_group_field()
        if not group_field:
            raise UserError(_("No group approval field was found on this rule to sync dynamic approvers."))

        candidate_groups = users.mapped("groups_id")
        if not candidate_groups:
            raise UserError(_("Dynamic approvers do not belong to any group to fill Group Approval."))

        group_field_type = group_field.type
        if group_field_type == "many2one":
            self.write({group_field_name: candidate_groups[0].id})
        elif group_field_type == "many2many":
            self.write({group_field_name: [(6, 0, candidate_groups.ids)]})
        else:
            raise UserError(_("Unsupported Group Approval field type for dynamic sync."))

        return users

    @api.model
    def _get_approval_spec(self, model, spec):
        model_name, map_rules, results = super()._get_approval_spec(model, spec)

        def _payload_id(x):
            """x can be an int id or a dict containing an 'id'."""
            if isinstance(x, int):
                return x
            if isinstance(x, dict):
                return x.get("id")
            return None

        def _entry_rule_id(entry):
            """
            entry can be:
              - dict with 'rule_id' as [id, name] (many2one style)
              - dict with 'rule_id' as int (rare)
              - int (entry id)  -> we won't be able to filter safely without reading it
            """
            if not isinstance(entry, dict):
                return None
            rid = entry.get("rule_id")
            if isinstance(rid, (list, tuple)) and rid:
                return rid[0]
            if isinstance(rid, int):
                return rid
            return None

        for key, bucket in list(results.items()):
            res_id = key[0]
            if not res_id:
                continue

            record = self.env[model].browse(res_id)

            # --- filter rules (bucket['rules'] can contain dicts or ints) ---
            filtered_rules_payload = []
            valid_rule_ids = set()

            for rule_data in bucket.get("rules", []) or []:
                rid = _payload_id(rule_data)
                if not rid:
                    continue

                rule = self.browse(rid)
                # IMPORTANT: read domain/python_code from the rule record (not from payload)
                if rule._match_rule_with_python(record, rule.domain, rule.python_code):
                    filtered_rules_payload.append(rule_data)
                    valid_rule_ids.add(rid)

            if not filtered_rules_payload:
                results.pop(key, None)
                continue

            bucket["rules"] = filtered_rules_payload

            # --- filter entries safely when entry is a dict (keep ints as-is to avoid breaking) ---
            new_entries = []
            for entry in bucket.get("entries", []) or []:
                erid = _entry_rule_id(entry)
                if erid is None:
                    # If entry isn't a dict (e.g., it's an int), we keep it to avoid
                    # accidentally dropping required entries without being able to inspect.
                    new_entries.append(entry)
                    continue
                if erid in valid_rule_ids:
                    new_entries.append(entry)

            bucket["entries"] = new_entries

        return model_name, map_rules, results

    # @api.model
    # def _get_approval_spec(self, model, spec):
    #     model_name, map_rules, results = super()._get_approval_spec(model, spec)
    #     for key, bucket in list(results.items()):
    #         res_id = key[0]
    #         if not res_id:
    #             continue
    #         record = self.env[model].browse(res_id)
    #         filtered_rules = []
    #         for rule_data in bucket.get("rules", []):
    #             rule = self.browse(rule_data["id"])
    #             if rule._match_rule_with_python(record, rule_data.get("domain"), rule_data.get("python_code")):
    #                 filtered_rules.append(rule_data)
    #         if filtered_rules:
    #             bucket["rules"] = filtered_rules
    #             valid_rule_ids = {r["id"] for r in filtered_rules}
    #             bucket["entries"] = [
    #                 entry for entry in bucket.get("entries", [])
    #                 if entry.get("rule_id") and entry["rule_id"][0] in valid_rule_ids
    #             ]
    #         else:
    #             results.pop(key, None)
    #     return model_name, map_rules, results

    @api.model
    def check_approval(self, model, res_id, method, action_id):
        result = super().check_approval(model, res_id, method, action_id)

        rules_payload = result.get("rules") or []
        if not rules_payload:
            return result

        record = self.env[model].browse(res_id)

        def _payload_id(x):
            """x can be int (id) or dict with key 'id'."""
            if isinstance(x, int):
                return x
            if isinstance(x, dict):
                return x.get("id")
            return None

        Entry = self.env["studio.approval.entry"]

        def _entry_rule_id(entry):
            """Return rule_id (int) for entry payload (dict/int), or None."""
            if isinstance(entry, int):
                e = Entry.browse(entry)
                return e.rule_id.id if e.exists() and e.rule_id else None

            if isinstance(entry, dict):
                rid = entry.get("rule_id")
                # many2one payload style: [id, name]
                if isinstance(rid, (list, tuple)) and rid:
                    return rid[0]
                # sometimes it can already be int
                if isinstance(rid, int):
                    return rid
            return None

        def _entry_is_approved(entry):
            """Return approved flag for entry payload (dict/int)."""
            if isinstance(entry, int):
                e = Entry.browse(entry)
                # در نسخه‌های مختلف ممکنه فیلدها فرق کنه؛ ولی معمولاً 'approved' هست
                return bool(getattr(e, "approved", False)) if e.exists() else False

            if isinstance(entry, dict):
                # معمولاً کلید 'approved' هست
                return bool(entry.get("approved"))
            return False

        # 1) Filter rules based on python condition (ALWAYS read from rule record)
        filtered_rules_payload = []
        valid_rule_ids = set()

        for rule_data in rules_payload:
            rid = _payload_id(rule_data)
            if not rid:
                continue
            rule = self.browse(rid)
            if rule._match_rule_with_python(record, rule.domain, rule.python_code):
                filtered_rules_payload.append(rule_data)
                valid_rule_ids.add(rid)

        if not filtered_rules_payload:
            # If no rules remain after filtering, treat as approved
            return {"approved": True, "rules": [], "entries": []}

        result["rules"] = filtered_rules_payload

        # 2) Filter entries so only entries belonging to remaining rules stay
        entries_payload = result.get("entries") or []
        filtered_entries = []
        for entry in entries_payload:
            erid = _entry_rule_id(entry)
            if erid is None:
                # اگر نتونستیم rule_id رو بفهمیم، برای جلوگیری از رفتار غیرمنتظره نگه می‌داریم
                # (می‌تونی اگر خواستی strict کنی، اینجا drop کنی)
                filtered_entries.append(entry)
                continue
            if erid in valid_rule_ids:
                filtered_entries.append(entry)

        result["entries"] = filtered_entries

        # 3) Compute approved status per remaining rule
        approved_by_rule = {rid: False for rid in valid_rule_ids}
        for entry in filtered_entries:
            erid = _entry_rule_id(entry)
            if erid in approved_by_rule:
                approved_by_rule[erid] = _entry_is_approved(entry)

        result["approved"] = all(approved_by_rule.values())
        return result

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
                if not self.browse(rule["id"])._match_rule_with_python(record, rule.get("domain"),
                                                                       rule.get("python_code")):
                    continue
                if rule["can_validate"]:
                    can_revoke = True
                    break

            if not can_revoke:
                raise UserError(
                    _("You cannot cancel an approval you didn't set yourself or you don't belong to an higher level rule's approvers."))
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
            rule_limitation_msg = _(
                'You can not approve this rule because another rule has already been approved/rejected.')
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
                if not self.browse(rule["id"])._match_rule_with_python(record, rule.get("domain"),
                                                                       rule.get("python_code")):
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

    def _create_request(self, res_id):
        self.ensure_one()
        rule_sudo = self.sudo()
        if not self.model_id.sudo().is_mail_activity:
            return False

        record = self.env[rule_sudo.model_name].browse(res_id)
        if not rule_sudo._match_rule_with_python(record, rule_sudo.domain, rule_sudo.python_code):
            return False

        users = rule_sudo._sync_dynamic_approvers_and_group(record)
        # When dynamic notify code is configured, those users should also receive
        # approval requests early in the process so they can act before completion.
        if rule_sudo.notify_python_code:
            users |= rule_sudo._eval_dynamic_users(
                record,
                rule_sudo.notify_python_code,
                _("Notify Approver Python Condition"),
            )
        if not users:
            return False

        requests = self.env['studio.approval.request'].sudo().search([
            ('rule_id', '=', self.id),
            ('res_id', '=', res_id),
        ])
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
                if not approval_rule._match_rule_with_python(record, approval_rule.domain, approval_rule.python_code):
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

        # `super()` relies on `approver_ids` to build approval requests. For
        # dynamic routing we temporarily project computed users to that field,
        # then restore the original configuration.
        original_approver_ids = rule_sudo.approver_ids.ids
        computed_approver_ids = users.ids
        if set(computed_approver_ids) != set(original_approver_ids):
            rule_sudo.write({'approver_ids': [(6, 0, computed_approver_ids)]})
            try:
                return super()._create_request(res_id)
            finally:
                rule_sudo.write({'approver_ids': [(6, 0, original_approver_ids)]})

        return super()._create_request(res_id)


class StudioApprovalEntryDynamic(models.Model):
    _inherit = "studio.approval.entry"

    def _notify_approval(self):
        for entry in self:
            if not entry.rule_id.model_id.is_mail_thread:
                continue
            record = self.env[entry.model].browse(entry.res_id)
            notify_users = entry.rule_id._resolve_dynamic_notify_users(record)
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
