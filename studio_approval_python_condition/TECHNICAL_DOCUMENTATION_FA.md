# مستند فنی (فارسی) — Studio Approval Python Condition

## معماری
این ماژول یک extension روی `studio.approval.rule` است و بدون تغییر مستقیم ماژول اصلی Studio عمل می‌کند.

اجزای اصلی:
1. **Model Extension** در `models/studio_approval_rule.py`
2. **View Inheritance** در `views/studio_approval_rule_views.xml`

## تغییرات مدل
### فیلدهای جدید
- `python_code` (Text): کد پایتون شرطی.
- `python_code_guide` (Text, compute, readonly): راهنمای ثابت متغیرهای قابل استفاده.

### متدهای کلیدی
- `_compute_python_code_guide`: پرکردن متن راهنما.
- `_compute_conditional`: فعال‌سازی conditional بر اساس `domain` یا `python_code`.
- `_check_python_code`: بررسی syntax با `ast.parse`.
- `_is_rule_applicable`: ارزیابی نهایی Rule با ترکیب Domain + Python.

## منطق ارزیابی شرط
ترتیب اجرا:
1. Domain بررسی می‌شود (در صورت وجود).
2. اگر Domain رد شود، Rule رد می‌شود.
3. اگر Python خالی باشد، نتیجه True است.
4. اگر Python وجود داشته باشد، با `safe_eval(..., mode="exec")` اجرا می‌شود.
5. نتیجه از `localdict['result']` خوانده می‌شود.

## Context اجرایی کد پایتون
- `env`
- `user`
- `record`
- `rule`
- `result` (پیش‌فرض: `True`)

## مدیریت خطا
- خطای Syntax هنگام ذخیره Rule با `ValidationError`.
- خطای Runtime هنگام evaluate با `UserError` کاربرپسند.

## تغییرات UI
View inherited طوری تغییر داده شده که بعد از `domain`:
- یک `separator` با عنوان **Python Condition**
- یک `group` شامل:
  - `python_code_guide` (readonly)
  - `python_code` (editable)

این ساختار باعث نظم بیشتر و خوانایی بهتر فرم می‌شود.

## سازگاری و ریسک
- سازگار با Ruleهای قبلی (Domain-only).
- در صورت خالی بودن `python_code` رفتار قبلی حفظ می‌شود.
- ریسک اصلی: نوشتن کد سنگین/اشتباه توسط ادمین؛ با syntax-check و runtime error handling کنترل شده است.
