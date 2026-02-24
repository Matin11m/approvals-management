# سناریوی تست کامل (فارسی) — منطق جدید Dynamic Approver/Notify

## 1) هدف تست
اعتبارسنجی کامل اینکه:
1. با `python_code` بتوان approverها را داینامیک تعیین کرد.
2. با `notify_python_code` بتوان دریافت‌کنندگان notify را داینامیک تعیین کرد.
3. هر دو منطق مستقل از هم کار کنند.
4. fallback به فیلدهای استاندارد (`approver_ids` و `users_to_notify`) برقرار باشد.

---

## 2) پیش‌نیازها
1. Odoo در حال اجرا.
2. ماژول‌های `web_studio` و `studio_approval_python_condition` نصب باشند.
3. مدل تست: `sale.order`.
4. کاربران تست:
   - `Requester`
   - `Approver A`
   - `Approver B`
   - `Notify A`
   - `Notify B`
5. روی Sales Team اعضا طوری تنظیم شوند که `record.team_id.member_ids` قابل استفاده باشد.

---

## 3) شناسنامه فیلدها (Field-by-Field)

| نام فیلد | نوع | ورودی/خروجی | مثال | نقش |
|---|---|---|---|---|
| `domain` | Char | ورودی | `[('company_id', '=', user.company_id.id)]` | فیلتر اولیه رکورد Rule |
| `python_code_guide` | Text readonly | خروجی نمایشی | راهنما | فقط توضیح متغیرها و نمونه |
| `python_code` | Text | ورودی کد | `result = record.user_id` | محاسبه Approverهای داینامیک |
| `notify_python_code` | Text | ورودی کد | `result = record.team_id.member_ids` | محاسبه Notifyهای داینامیک |
| `result` | متغیر runtime | خروجی کد | user/user_ids | باید کاربر/شناسه کاربر برگرداند |

### خروجی معتبر `result`
- `res.users`
- `int` (user id)
- `list/tuple/set[int]`
- `list` از `res.users`

---

## 4) سناریوهای تست گام‌به‌گام

## سناریو A — نمایش UI
### مراحل
1. مسیر **Studio > Approvals > Rule Form**.
2. بررسی کنید بعد از `domain` سه فیلد نمایش داده شود:
   - `Python Guide`
   - `Approver Python Condition`
   - `Notify Approver Python Condition`
3. readonly بودن Guide و editable بودن دو textbox را بررسی کنید.

### انتظار
- هر سه فیلد با ترتیب درست نمایش داده شوند.
- Guide غیرقابل ویرایش باشد.

---

## سناریو B — محاسبه Approver با python_code
### تنظیم Rule
- `python_code`:
```python
result = record.user_id
```
- `notify_python_code`: خالی

### مراحل
1. یک SO با Salesperson = `Approver A` بسازید.
2. تایید سند را trigger کنید.
3. چک کنید approval request برای `Approver A` ساخته شود.
4. SO جدید با Salesperson = `Approver B` بسازید.
5. تایید سند را trigger کنید.
6. چک کنید approval request برای `Approver B` ساخته شود.

### انتظار
- دریافت‌کننده approval request با تغییر رکورد تغییر کند (داینامیک per-record).

---

## سناریو C — محاسبه Notify با notify_python_code
### تنظیم Rule
- `python_code`: خالی (یا ثابت)
- `notify_python_code`:
```python
result = record.team_id.member_ids
```

### مراحل
1. یک سند را approve/reject کنید.
2. پیام notify ثبت‌شده روی chatter را بررسی کنید.
3. partnerهای پیام را با اعضای `team_id.member_ids` مقایسه کنید.

### انتظار
- notify گیرنده‌ها از کد `notify_python_code` محاسبه شوند.
- وابسته به رکورد باشند.

---

## سناریو D — استقلال دو منطق Approver و Notify
### تنظیم Rule
- `python_code`:
```python
result = record.user_id
```
- `notify_python_code`:
```python
result = [env.user.id]
```

### مراحل
1. عملیات approval را اجرا کنید.
2. بررسی کنید approver = `record.user_id`.
3. بررسی کنید notify recipient = کاربر جاری (`env.user`) باشد.

### انتظار
- approver و notify مستقل از هم resolve شوند.

---

## سناریو E — Fallback رفتار قدیمی
### تنظیم Rule
- `python_code`: خالی
- `notify_python_code`: خالی
- `approver_ids` و `users_to_notify` را دستی تنظیم کنید.

### مراحل
1. flow approval را اجرا کنید.
2. بررسی کنید recipients از فیلدهای استاندارد گرفته شوند.

### انتظار
- بدون کد پایتون، رفتار قبلی دقیقاً حفظ شود.

---

## سناریو F — خروجی نامعتبر در result
### تنظیم Rule
- `python_code`:
```python
result = "invalid"
```

### مراحل
1. trigger approval انجام دهید.

### انتظار
- خطای `UserError` کاربرپسند به دلیل نوع خروجی نامعتبر نمایش داده شود.

---

## سناریو G — خطای Syntax
### تنظیم Rule
- `notify_python_code` نامعتبر:
```python
result = [env.user.id
```

### مراحل
1. Rule را ذخیره کنید.

### انتظار
- خطای validation syntax نمایش داده شود و ذخیره انجام نشود.

---

## 5) چک‌لیست رگرسیون
- Domain-only ruleها سالم باشند.
- notification order و step sequencing به‌هم نریزد.
- revoke/approve/request flow دچار رگرسیون نشود.
- Ruleهای بدون کد پایتون همچنان کار کنند.

---

## 6) خروجی نهایی مورد انتظار
- admin بتواند با دو textbox مستقل، Approver و Notify را داینامیک تعیین کند.
- خروجی‌ها per-record و قابل پیش‌بینی باشند.
- خطاهای syntax/runtime/type با پیام مناسب کنترل شوند.
