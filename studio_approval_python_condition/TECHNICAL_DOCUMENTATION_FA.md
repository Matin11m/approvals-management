# مستند فنی (فارسی) — Studio Approval Python Condition

## معماری
این ماژول یک افزونه روی `studio.approval.rule` و `studio.approval.entry` است و بدون تغییر مستقیم ماژول اصلی Studio کار می‌کند.

اجزای اصلی:
1. **Model Extension** در `models/studio_approval_rule.py`
2. **View Inheritance** در `views/studio_approval_rule_views.xml`

---

## مدل و فیلدها
### فیلدهای افزوده‌شده روی Rule
- `python_code` (Text): کد پایتون برای **محاسبه approverها**.
- `notify_python_code` (Text): کد پایتون برای **محاسبه کاربران notify**.
- `python_code_guide` (Text, readonly, compute): راهنمای readonly برای نوشتن کد.

### رفتار `result` در کد پایتون
در منطق جدید، `result` باید لیست/کاربر برگرداند (نه فقط bool).

خروجی‌های مجاز:
- رکورد `res.users`
- یک عدد (id کاربر)
- لیست/tuple/set از idها
- لیست شامل رکوردهای `res.users`

---

## متدهای کلیدی
- `_check_python_code`:
  - سینتکس هر دو فیلد `python_code` و `notify_python_code` را با `ast.parse` اعتبارسنجی می‌کند.
- `_extract_user_ids`:
  - خروجی `result` را normalize می‌کند و به لیست id کاربر تبدیل می‌کند.
- `_eval_user_python_code`:
  - کد پایتون را با `safe_eval` اجرا می‌کند و خروجی را به `res.users` معتبر تبدیل می‌کند.
- `_get_rule_approvers(record)`:
  - approverها را از `python_code` (یا fallback به `approver_ids`) برمی‌گرداند.
- `_get_rule_notify_users(record)`:
  - کاربران notify را از `notify_python_code` (یا fallback به `users_to_notify`) برمی‌گرداند.

---

## نقاط اتصال به Flow اصلی Approval
1. **در `_get_approval_spec`**:
   - به ازای هر رکورد، `approver_ids` و `users_to_notify` به‌صورت داینامیک از کد پایتون پر می‌شوند.
2. **در `_create_request`**:
   - activity/request برای approverهای داینامیک ساخته می‌شود.
3. **در `studio.approval.entry._notify_approval` (override)**:
   - گیرنده‌های پیام notify به‌صورت داینامیک از `notify_python_code` محاسبه می‌شوند.

---

## Context اجرایی کد پایتون
متغیرهای قابل استفاده:
- `env`
- `user`
- `record`
- `rule`
- `result`

نمونه:
```python
result = record.user_id
```

```python
result = record.team_id.member_ids
```

```python
result = [env.user.id]
```

---

## مدیریت خطا
- **Syntax Error** در زمان ذخیره Rule با `ValidationError`.
- **Runtime Error** در زمان اجرای کد با `UserError`.
- **Type Error در خروجی result** (نوع نامعتبر) با `UserError` کاربرپسند.

---

## سازگاری
- اگر `python_code` خالی باشد، approverها از `approver_ids` عادی گرفته می‌شوند.
- اگر `notify_python_code` خالی باشد، notifyها از `users_to_notify` عادی گرفته می‌شوند.
- Ruleهای قدیمی بدون کد پایتون بدون تغییر رفتار می‌کنند.
