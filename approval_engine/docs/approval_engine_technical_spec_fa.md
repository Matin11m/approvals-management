# مستند فنی ماژول Approval Engine (Odoo 19)

## 1) هدف معماری
`approval_engine` یک اپلیکیشن مستقل برای مدیریت تاییدیه‌های generic است که:
- فرم/دسته‌های ماژول `approvals` را ingest می‌کند.
- هر قالب تایید را به هر مدل از Odoo متصل می‌کند.
- محل اعمال تاییدیه را در سطح view + method تعریف می‌کند.

---

## 2) وابستگی‌ها و بارگذاری
- وابستگی‌ها:
  - `base`
  - `mail`
  - `approvals`
- فایل‌های داده:
  - گروه‌ها و ACL
  - sequence درخواست
  - bootstrap برای sync اولیه از `approval.category`

در bootstrap، متد `action_sync_from_approvals` اجرا می‌شود تا categoryهای approvals به templateهای اولیه‌ی engine تبدیل شوند.

---

## 3) مدل‌های داده

### 3.1) `approval.engine.template`
هسته‌ی پیکربندی تاییدیه:
- `approval_category_id`: لینک به فرم/دسته Approvals.
- `model_id` / `model`: مدل هدف برای اعمال تاییدیه.
- `rule_type`: `always | domain | python`.
- `rule_domain`, `rule_python`: منطق انتخاب template.
- `on_approved_method`, `on_rejected_method`: hook روی رکورد مقصد.
- `step_ids`: مراحل تایید.
- `binding_ids`: نگاشت UI (view/function).

اعتبارسنجی‌ها:
- الزامی بودن domain/python براساس `rule_type`.
- داشتن حداقل یک step برای template فعال.
- اعتبار نام methodها (`isidentifier`).

### 3.2) `approval.engine.step`
- تعریف مرحله تایید با:
  - گروه تاییدکننده
  - ترتیب
  - `min_approvals`
  - امکان `require_all_group_users`

### 3.3) `approval.engine.binding`
- نگاشت نقطه‌ی اعمال تاییدیه در UI:
  - `view_id` از `ir.ui.view`
  - `trigger_method`
  - `button_label`
- دامنه `view_id` براساس مدل template محدود می‌شود.

### 3.4) `approval.engine.request`
اجرای واقعی جریان تایید روی یک رکورد:
- لینک رکورد با `res_model` + `res_id`
- state machine:
  - `draft`
  - `waiting`
  - `approved`
  - `rejected`
  - `cancelled`
- `current_step_id` برای مرحله جاری
- log تصمیم‌ها در `approval.engine.log`

### 3.5) `approval.engine.log`
ثبت audit trail تصمیم‌ها:
- چه کسی
- کدام مرحله
- approve/reject
- توضیح
- زمان

---

## 4) جریان‌های کلیدی

### 4.1) Sync اولیه از Approvals
1. ماژول نصب می‌شود.
2. `action_sync_from_approvals` categoryهای `approval.category` را می‌خواند.
3. برای موارد جدید، template غیرفعال می‌سازد تا ادمین model/step/binding را کامل کند.

### 4.2) پیدا کردن template روی رکورد
در mixin:
1. templateهای active برای مدل جاری خوانده می‌شوند.
2. rule هر template ارزیابی می‌شود.
3. اولین template match شده انتخاب می‌شود.

### 4.3) ارسال برای تایید
1. رکورد مقصد متد `action_submit_for_approval` را صدا می‌زند.
2. request ساخته می‌شود.
3. state به `waiting` می‌رود و step اول فعال می‌شود.

### 4.4) تایید/رد
- تاییدکننده فقط اگر در گروه step باشد می‌تواند تصمیم بگیرد.
- برای approve:
  - log ثبت می‌شود.
  - اگر شرط تکمیل step برقرار بود، به step بعدی می‌رود یا نهایی approved می‌شود.
- برای reject:
  - log ثبت می‌شود.
  - request به `rejected` می‌رود.
  - hook رد اجرا می‌شود (در صورت تنظیم).

---

## 5) امنیت و دسترسی (وضعیت فعلی)
- در فاز فعلی، سیاست امنیتی به‌صورت ساده/موقت اعمال شده است:
- دسترسی پایه برای کاربران داخلی (`base.group_user`) فعال است تا منوهای اصلی قابل استفاده باشند.
- تفکیک نقش‌ها و Ruleهای دقیق امنیتی به فاز hardening بعدی موکول شده است.
- در فاز production باید ACL/Record Rules دقیق تعریف و فعال شوند.

---

## 6) UI و ناوبری
منوهای اصلی اپ:
- `Requests`
- `Approvals Forms`
- `Templates`

در فرم template:
- فیلد فرم مبدا approvals
- فیلد مدل هدف
- تنظیم rule
- تب مراحل (Steps)
- تب نگاشت UI (UI Bindings)

---

## 7) محدودیت‌های فعلی (Known Gaps)
- Binding فعلاً metadata است و هنوز inject خودکار دکمه در view انجام نمی‌دهد.
- Rule Editor پیشرفته (UI builder) برای Domain/Python پیاده نشده.
- Policyهای پیشرفته مانند delegation/escalation SLA فعلاً اضافه نشده‌اند.

---

## 8) پیشنهاد فاز بعد
1. موتور view-injection امن برای افزودن دکمه بر اساس binding.
2. Rule Builder گرافیکی.
3. SLA + escalation job.
4. Versioning template و migration rule.
5. گزارش KPI تاییدیه‌ها.
