# مستند فنی (Technical) — Approval Engine

## 1) هدف و Scope
ماژول `approval_engine` یک موتور تایید عمومی (Generic) برای Odoo 19 است که:
- فرم‌های Approvals را به Templateهای قابل اجرا تبدیل می‌کند.
- روی هر مدل کسب‌وکاری (`ir.model`) قابل اعمال است.
- گردش تایید مرحله‌ای + لاگ کامل تصمیم‌ها ارائه می‌دهد.
- برای هر درخواست، Rule سفارشی پایتونی (Execute Code) اجرا می‌کند.

---

## 2) معماری کلان
### 2.1 مدل‌های اصلی
- `approval.engine.template`
- `approval.engine.step`
- `approval.engine.binding`
- `approval.engine.request`
- `approval.engine.log`
- `approval.engine.mixin` (Abstract integration layer)

### 2.2 وابستگی‌ها
- `base`
- `mail`
- `approvals`

### 2.3 فایل‌های داده
- `data/sequence.xml`: شماره‌گذاری Request
- `data/bootstrap.xml`: sync اولیه categoryهای approvals
- `security/ir.model.access.csv`: دسترسی پایه کاربران داخلی

---

## 3) Data Dictionary (فیلد به فیلد)

## 3.1 `approval.engine.template`
- `name (Char, required)`: نام قالب تایید.
- `active (Boolean)`: فعال/غیرفعال بودن قالب.
- `sequence (Integer)`: اولویت انتخاب قالب (کمتر = اولویت بالاتر).
- `company_id (Many2one: res.company)`: شرکت مالک قالب.
- `approval_category_id (Many2one: approval.category)`: فرم مبدا از Approvals.
- `model_id (Many2one: ir.model, required)`: مدل هدف.
- `model (Char, related)`: technical name مدل هدف.
- `description (Text)`: توضیحات داخلی.
- `rule_type (Selection)`: نوع Rule (`always/domain/python`).
- `rule_domain (Text)`: دامنه فیلتر در حالت domain.
- `rule_python (Text)`: expression پایتونی در حالت python.
- `on_approved_method (Char)`: متد رکورد هدف بعد از تایید نهایی.
- `on_rejected_method (Char)`: متد رکورد هدف بعد از رد.
- `step_ids (One2many)`: مراحل تایید.
- `binding_ids (One2many)`: نگاشت‌های view/method.

**Validationها**
- برای `rule_type=domain` مقدار `rule_domain` الزامی است.
- برای `rule_type=python` مقدار `rule_python` الزامی است.
- قالب active باید حداقل یک step داشته باشد.

## 3.2 `approval.engine.step`
- `name (Char, required)`: نام مرحله.
- `template_id (Many2one, required)`: ارجاع به قالب.
- `sequence (Integer)`: ترتیب مرحله.
- `approver_group_id (Many2one: res.groups, required)`: گروه تاییدکننده.
- `min_approvals (Integer, default=1)`: حداقل تعداد تایید لازم.
- `require_all_group_users (Boolean)`: اگر true، همه اعضای گروه باید تایید کنند.

## 3.3 `approval.engine.binding`
- `sequence (Integer)`: ترتیب binding.
- `template_id (Many2one, required)`: قالب مرتبط.
- `model_id (Many2one, related)`: مدل هدف.
- `model (Char, related)`: technical model name.
- `view_id (Many2one: ir.ui.view, required)`: ویوی هدف.
- `trigger_method (Char, required)`: متد آغازگر submit.
- `button_label (Char)`: متن دکمه (metadata).

## 3.4 `approval.engine.request`
- `name (Char)`: شناسه request از sequence.
- `company_id (Many2one)`: شرکت.
- `template_id (Many2one, required)`: قالب اعمال‌شده.
- `state (Selection)`: وضعیت (`draft/waiting/approved/rejected/cancelled`).
- `res_model (Char, required)`: مدل رکورد هدف.
- `res_id (Integer, required)`: شناسه رکورد هدف.
- `reference (Reference, computed)`: نمایش رکورد هدف.
- `requester_id (Many2one: res.users)`: درخواست‌دهنده.
- `current_step_id (Many2one)`: مرحله جاری تایید.
- `log_ids (One2many)`: لاگ تصمیم‌ها.

### فیلدهای Python Rule روی Request
- `python_rule_mode (Selection)`:
  - `none`: غیرفعال
  - `manual`: فقط اجرای دستی
  - `approve`: اجرا قبل از approve
  - `reject`: اجرا قبل از reject
  - `both`: اجرا قبل از approve/reject
- `python_rule_code (Text)`: کد پایتون قابل اجرا.
- `python_last_result (Char)`: آخرین وضعیت (`allowed/blocked/error`).
- `python_last_log (Text)`: پیام/خطای آخر اجرا.

## 3.5 `approval.engine.log`
- `request_id`: request مرتبط.
- `step_id`: مرحله مربوطه.
- `user_id`: تصمیم‌گیرنده.
- `action`: `approved/rejected`.
- `comment`: توضیحات تصمیم.

---

## 4) Runtime Flow
1. Submit -> state=`waiting` + تعیین `current_step_id`.
2. Approve:
   - (اختیاری) اجرای Python Rule با action=`approve`.
   - اعتبارسنجی عضویت کاربر در گروه مرحله.
   - ثبت log approve.
   - بررسی تکمیل مرحله.
3. Reject:
   - (اختیاری) اجرای Python Rule با action=`reject`.
   - ثبت log reject + state=`rejected`.
4. Finalization:
   - اجرای hook `on_approved_method` یا `on_rejected_method` روی رکورد هدف.

---

## 5) قرارداد اجرای Python Code
- Engine: `safe_eval(..., mode='exec')`
- Local context:
  - `request`, `record`, `env`, `user`, `action`
  - `result=True` (پیش‌فرض)
  - `message=''` (اختیاری)
- اگر کد خطا بدهد: `python_last_result=error` و `UserError`.
- اگر `result=False`: action بلاک + پیام کاربر از `message`.

---

## 6) محدودیت‌ها / Known Gaps
- Binding فعلاً metadata است (view injection کامل اتوماتیک ندارد).
- Rule Builder گرافیکی Studio-like موجود نیست.
- امنیت production-level (تفکیک نقش ریز) نیازمند hardening جداگانه است.
