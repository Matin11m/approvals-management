# راهنمای کاربر (User Guide) — Approval Engine

## 1) ورود به ماژول
1. Apps -> نصب `Approval Engine`
2. از App Launcher وارد اپ شوید.
3. منوهای اصلی:
   - `Approvals Forms`
   - `Templates`
   - `Requests`

## 2) راه‌اندازی سریع
### قدم 1: ساخت Template
- مسیر: `Templates`
- فیلدها:
  - `Approvals Form`
  - `Model`
  - `Rule Type`

### قدم 2: تعریف Steps
- حداقل یک step الزامی است.
- برای هر step:
  - گروه تاییدکننده
  - حداقل تعداد تایید

### قدم 3: فعال‌سازی
- Template را `Active` کنید.

## 3) کار با Request
1. رکورد business را submit کنید.
2. در `Requests` وضعیت را دنبال کنید.
3. Approverها approve/reject انجام دهند.
4. لاگ‌ها در تب Logs ثبت می‌شوند.

## 4) استفاده از Python Rules
در فرم Request -> تب `Python Rules`:
- `Python Rule Mode`:
  - `none`, `manual`, `approve`, `reject`, `both`
- `Python Execute Code`

### مثال
```python
if record and record.amount_total > 10000:
    result = False
    message = 'Amount is over allowed threshold.'
```

### تست دستی
- mode را `manual` بگذارید.
- دکمه `Run Python Rule` را بزنید.
- خروجی در `python_last_result` و `python_last_log` دیده می‌شود.

## 5) خطاهای رایج
- Template فعال بدون Step -> خطای validation
- کاربر خارج از گروه step -> خطای دسترسی approve/reject
- خطای syntax در python code -> ثبت خطا و block action
