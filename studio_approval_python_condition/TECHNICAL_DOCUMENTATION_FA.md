# مستند فنی (فارسی) — UI تب‌دار + راهنمای readonly

## تغییرات کلیدی
1. فرم Rule بعد از `domain` دارای `notebook` با دو تب است:
   - `Approver Python`
   - `Notify Python`
2. برای هر تب راهنما به دو بخش readonly شکسته شده است:
   - بخش قوانین/متغیرها
   - بخش مثال‌ها

   فیلدها:
   - `approver_python_code_guide`
   - `approver_python_examples_guide`
   - `notify_python_code_guide`
   - `notify_python_examples_guide`
3. فیلدهای کد:
   - `python_code` برای Approver
   - `notify_python_code` برای Notify

---

## فیلدهای جدید مدل
- `approver_python_code_guide` (Text, compute, readonly)
- `approver_python_examples_guide` (Text, compute, readonly)
- `notify_python_code_guide` (Text, compute, readonly)
- `notify_python_examples_guide` (Text, compute, readonly)

این چهار فیلد در متد `_compute_python_code_guides` مقداردهی می‌شوند.

---

## منطق اجرایی (بدون تغییر مفهومی)
- `python_code` همچنان Approverهای داینامیک را resolve می‌کند.
- `notify_python_code` همچنان کاربران Notify داینامیک را resolve می‌کند.
- خروجی `result` باید user/user_ids باشد (نه bool صرف).

---

## مزیت تغییر
- تمیزتر شدن UI
- تفکیک واضح مسئولیت‌ها بین Approver و Notify
- راهنمای درجا (readonly) برای هر تب و کاهش خطای کاربر
