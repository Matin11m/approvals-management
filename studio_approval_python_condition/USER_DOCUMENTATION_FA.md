# راهنمای کاربر (فارسی) — بخش‌های Approver/Notify Python

## تغییر جدید UI
در فرم Rule، بعد از `domain` یک بخش‌بندی‌شده اضافه شده است:
1. بخش **Approver Python**
2. بخش **Notify Python**

در هر بخش:
- یک راهنمای readonly بخش اول: متغیرها و خروجی مجاز
- یک راهنمای readonly بخش دوم: مثال‌های آماده
- یک textbox برای کد پایتون

---

## بخش Approver Python
- فیلد راهنما (بخش قوانین): `approver_python_code_guide` (readonly)
- فیلد راهنما (بخش مثال‌ها): `approver_python_examples_guide` (readonly)
- فیلد کد: `python_code`
- هدف: تعیین داینامیک Approverها

نمونه:
```python
result = record.user_id
```

---

## بخش Notify Python
- فیلد راهنما (بخش قوانین): `notify_python_code_guide` (readonly)
- فیلد راهنما (بخش مثال‌ها): `notify_python_examples_guide` (readonly)
- فیلد کد: `notify_python_code`
- هدف: تعیین داینامیک کاربران Notify

نمونه:
```python
result = record.team_id.member_ids
```

---

## متغیرهای قابل استفاده در هر دو بخش
- `env`
- `user`
- `record`
- `rule`
- `result`

## خروجی مجاز `result`
- `res.users` recordset
- `int` (شناسه کاربر)
- `list/tuple/set` از شناسه کاربران

## نکات
- اگر `python_code` خالی باشد، از `approver_ids` عادی استفاده می‌شود.
- اگر `notify_python_code` خالی باشد، از `users_to_notify` عادی استفاده می‌شود.
- خطای syntax یا خروجی نامعتبر، خطای کاربرپسند می‌دهد.
