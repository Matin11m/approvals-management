# مستند فنی (Technical) — Approval Engine

## 1) هدف ماژول
`approval_engine` یک موتور تایید عمومی برای Odoo 19 است که:
- فرم‌های approvals را به templateهای قابل استفاده تبدیل می‌کند.
- روی هر مدل Odoo قابل اعمال است.
- تایید مرحله‌ای، لاگ تصمیم و hook اجرایی دارد.
- روی هر request از Python execute-code برای قوانین سفارشی پشتیبانی می‌کند.

## 2) معماری داده
### 2.1 مدل‌ها
- `approval.engine.template`: تنظیمات قالب تایید.
- `approval.engine.step`: مراحل تایید با گروه/حداقل تایید.
- `approval.engine.binding`: نگاشت metadata برای view/method هدف.
- `approval.engine.request`: نمونه اجرایی تایید روی رکورد واقعی.
- `approval.engine.log`: لاگ approve/reject.
- `approval.engine.mixin`: API اتصال به مدل‌های بیزینسی.

### 2.2 فیلدهای مهم Request
- `state`: `draft/waiting/approved/rejected/cancelled`
- `res_model`, `res_id`
- `current_step_id`
- `python_rule_mode`
- `python_rule_code`
- `python_last_result`, `python_last_log`

## 3) جریان اجرای تایید
1. submit -> request به `waiting` می‌رود.
2. approve/reject فقط توسط اعضای گروه step جاری.
3. با تکمیل step، به step بعدی یا `approved` نهایی.
4. در approve/reject نهایی، hook template روی رکورد مقصد اجرا می‌شود.

## 4) اجرای Python Rule
- موتور: `safe_eval(mode='exec')`
- context مجاز:
  - `request`, `record`, `env`, `user`, `action`
- قرارداد خروجی:
  - `result = True/False`
  - `message = '...'` (اختیاری)
- behavior:
  - اگر `result=False` -> action بلاک می‌شود.
  - خروجی/خطا در `python_last_result/python_last_log` ذخیره می‌شود.

## 5) ملاحظات امنیتی
- در فاز فعلی، policy ساده برای `base.group_user` فعال است.
- برای production:
  - ACL/Record Rule دقیق
  - محدودسازی edit Python code به نقش فنی
  - audit کامل تغییرات کد

## 6) محدودیت‌های فعلی
- binding فعلاً metadata است و view injection اتوماتیک کامل ندارد.
- rule builder گرافیکی (Studio-like) هنوز پیاده نشده.

## 7) مسیر توسعه بعدی
- Rule test wizard در UI
- versioning برای template/rule
- escalation/SLA
- parity کامل با Studio export mapping
