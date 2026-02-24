# مستند فنی ماژول یکپارچه Approval Engine

## هدف
ایجاد یک ماژول واحد برای مدیریت کامل تاییدات + اجرای کد پایتون سفارشی روی هر درخواست.

## اجزای اصلی
- `approval.engine.template`
- `approval.engine.step`
- `approval.engine.binding`
- `approval.engine.request`
- `approval.engine.log`
- `approval.engine.mixin`

## قابلیت Execute Python Rule (داخل همان ماژول)
در مدل `approval.engine.request`:
- `python_rule_mode`: `none/manual/approve/reject/both`
- `python_rule_code`
- `python_last_result`
- `python_last_log`

## موتور اجرا
- با `safe_eval(..., mode='exec')`
- context: `request`, `record`, `env`, `user`, `action`
- قرارداد خروجی:
  - `result` (bool)
  - `message` (str)

## رفتار runtime
- اگر mode روی approve/reject/both باشد، قبل از action اصلی کد اجرا می‌شود.
- اگر `result=False` باشد، اکشن بلاک می‌شود.
- نتیجه/خطا در فیلدهای last_result/last_log ذخیره می‌شود.
