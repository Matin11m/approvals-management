# سناریوی تست کامل (فارسی) — ساختار جدید تب‌ها

## هدف
تست اینکه:
1. UI به صورت دو تب مستقل نمایش داده می‌شود.
2. راهنمای readonly در هر تب درست نمایش داده می‌شود.
3. منطق Approver و Notify به‌صورت مستقل کار می‌کند.

---

## پیش‌نیاز
- ماژول نصب باشد.
- Odoo بالا باشد.
- مدل تست: `sale.order`
- کاربران تست: `Requester`, `Approver A`, `Notify A`

---

## سناریو 1 — بررسی UI تب‌ها
### مراحل
1. Rule فرم را باز کنید.
2. بعد از `domain` وجود `notebook` را بررسی کنید.
3. بررسی کنید دو تب زیر وجود داشته باشد:
   - `Approver Python`
   - `Notify Python`
4. داخل هر تب readonly guide را بررسی کنید.

### انتظار
- هر دو تب دیده شوند.
- guide هر تب readonly باشد.

---

## سناریو 2 — Approver از تب اول
### تنظیم
تب `Approver Python`:
```python
result = record.user_id
```

### انتظار
- approval request به کاربر `record.user_id` برود.

---

## سناریو 3 — Notify از تب دوم
### تنظیم
تب `Notify Python`:
```python
result = record.team_id.member_ids
```

### انتظار
- پیام notify به اعضای تیم ارسال شود.

---

## سناریو 4 — استقلال دو تب
### تنظیم
Approver:
```python
result = record.user_id
```
Notify:
```python
result = [env.user.id]
```

### انتظار
- گیرنده Approver و Notify متفاوت و مستقل resolve شوند.

---

## سناریو 5 — خطای syntax در هر تب
### تنظیم
در یکی از تب‌ها کد نامعتبر بگذارید:
```python
result = [env.user.id
```

### انتظار
- خطای validation نمایش داده شود و Rule ذخیره نشود.

---

## سناریو 6 — fallback
### تنظیم
- `python_code` خالی
- `notify_python_code` خالی

### انتظار
- سیستم از `approver_ids` و `users_to_notify` استاندارد استفاده کند.
