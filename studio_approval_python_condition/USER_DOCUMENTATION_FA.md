# راهنمای کاربر (فارسی) — تنظیم Approver و Notify با Python

## این قابلیت چه کاری می‌کند؟
در Rule تایید، می‌توانید با کد پایتون مشخص کنید:
1. چه کاربرانی **Approver** باشند.
2. چه کاربرانی **Notify** دریافت کنند.

این دو کاملاً جدا از هم هستند.

---

## محل فیلدها
مسیر: **Studio > Approvals > Rule Form**

بعد از Domain این فیلدها را می‌بینید:
- `Python Guide` (readonly)
- `Approver Python Condition` (`python_code`)
- `Notify Approver Python Condition` (`notify_python_code`)

---

## متغیرهای قابل استفاده در کد
- `env`
- `user`
- `record`
- `rule`
- `result`

> باید خروجی را داخل `result` قرار دهید.

---

## خروجی قابل قبول برای `result`
- `res.users` recordset
- یک id کاربر (عدد)
- لیست/tuple/set از id کاربران
- لیستی از رکوردهای `res.users`

نمونه‌های معتبر:
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

## مثال عملی
### 1) Approver شرطی
```python
# تاییدکننده = مدیر فروش سند
result = record.user_id
```

### 2) Notify شرطی
```python
# نوتیفای به اعضای تیم فروش
result = record.team_id.member_ids
```

---

## نکات مهم
- اگر `python_code` خالی باشد، سیستم از `Approvers` عادی Rule استفاده می‌کند.
- اگر `notify_python_code` خالی باشد، سیستم از `Users to Notify` عادی Rule استفاده می‌کند.
- خطای syntax باعث می‌شود Rule ذخیره نشود.
- خروجی نامعتبر (مثلاً string به‌جای user/id) خطای کاربرپسند می‌دهد.
