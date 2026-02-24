# راهنمای کاربر ماژول یکپارچه Approval Engine

## 1) نصب
1. ماژول `approval_engine` را نصب کنید.
2. وارد اپ Approval Engine شوید.

## 2) تنظیم اولیه
1. از Templates یک قالب بسازید.
2. Model هدف را انتخاب کنید.
3. در Steps مرحله‌ها را تعریف کنید.
4. قالب را Active کنید.

## 3) استفاده از Python Rule روی Request
1. یک Request باز کنید.
2. در تب `Python Rules`:
   - `Python Rule Mode` را انتخاب کنید.
   - کد را در `Python Execute Code` وارد کنید.
3. برای تست دستی، mode را `manual` بگذارید و `Run Python Rule` بزنید.

## 4) مثال کد
```python
if record and record.amount_total > 10000:
    result = False
    message = 'Amount is over allowed threshold.'
```

## 5) نتیجه
- اگر `result=False` باشد، Approve/Reject متوقف می‌شود.
- خروجی در `python_last_result` و `python_last_log` ثبت می‌شود.
