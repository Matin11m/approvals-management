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


---

## رفع خطای `UndefinedColumn` برای `notify_python_code`
اگر خطای زیر را دیدید:

`psycopg2.errors.UndefinedColumn: column studio_approval_rule.notify_python_code does not exist`

علت: کد جدید deploy شده ولی ماژول upgrade نشده و ستون DB هنوز ساخته نشده است.

### راه‌حل استاندارد (پیشنهادی)
ماژول را upgrade کنید تا ORM ستون‌های جدید را بسازد:

```bash
odoo-bin -d <db_name> -u studio_approval_python_condition --stop-after-init
```

### راه‌حل اضطراری (فقط برای مواقع خاص)
اگر لازم شد موقتاً دستی ستون را بسازید (بعدش باز هم upgrade انجام شود):

```sql
ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS notify_python_code text;
ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS approver_python_examples_guide text;
ALTER TABLE studio_approval_rule ADD COLUMN IF NOT EXISTS notify_python_examples_guide text;
```

> نکته: روش صحیح و پایدار همان upgrade ماژول است.
