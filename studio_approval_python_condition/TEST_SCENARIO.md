# سناریوی تست کامل (فارسی) — ساختار جدید بخش‌ها

## هدف
تست اینکه:
1. UI به صورت دو بخش مستقل نمایش داده می‌شود.
2. راهنمای readonly در هر بخش در دو بخش (قوانین + مثال‌ها) نمایش داده می‌شود.
3. منطق Approver و Notify به‌صورت مستقل کار می‌کند.

---

## پیش‌نیاز
- ماژول نصب باشد.
- Odoo بالا باشد.
- مدل تست: `sale.order`
- کاربران تست: `Requester`, `Approver A`, `Notify A`

---

## سناریو 1 — بررسی UI بخش‌ها
### مراحل
1. Rule فرم را باز کنید.
2. بعد از `domain` وجود `section` را بررسی کنید.
3. بررسی کنید دو بخش زیر وجود داشته باشد:
   - `Approver Python`
   - `Notify Python`
4. داخل هر بخش دو guide readonly را بررسی کنید (rules و examples).

### انتظار
- هر دو بخش دیده شوند.
- در هر بخش دو guide readonly نمایش داده شود.

---

## سناریو 2 — Approver از بخش اول
### تنظیم
بخش `Approver Python`:
```python
result = record.user_id
```

### انتظار
- approval request به کاربر `record.user_id` برود.

---

## سناریو 3 — Notify از بخش دوم
### تنظیم
بخش `Notify Python`:
```python
result = record.team_id.member_ids
```

### انتظار
- پیام notify به اعضای تیم ارسال شود.

---

## سناریو 4 — استقلال دو بخش
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

## سناریو 5 — خطای syntax در هر بخش
### تنظیم
در یکی از بخش‌ها کد نامعتبر بگذارید:
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
