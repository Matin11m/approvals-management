# مستند فنی — Studio Approval Dynamic Routing

این ماژول جدید، همان قابلیت‌های ماژول قبلی را به‌صورت مستقل ارائه می‌دهد، با نام ماژول و نام helperها تغییر یافته.

## موارد اصلی
- ماژول: `studio_approval_dynamic_routing`
- helperهای جدید:
  - `_match_rule_with_python`
  - `_normalize_dynamic_user_ids`
  - `_eval_dynamic_users`
  - `_resolve_dynamic_approvers`
  - `_resolve_dynamic_notify_users`
- pre-init hook برای ساخت ستون‌ها:
  - `python_code`
  - `notify_python_code`

## نکته سازگاری Owl
در `_get_approval_spec` و `check_approval` ابتدا `super()` صدا زده می‌شود تا payload استاندارد کلاینت حفظ شود.


## نکته Odoo 19 برای `pre_init_hook`
در Odoo 19، `pre_init_hook` ممکن است به‌جای cursor، آبجکت `Environment` دریافت کند.
به همین دلیل در hook از الگوی سازگار استفاده شده:
- اگر `env` آمد: از `env.cr`
- اگر `cr` آمد: مستقیم از همان

این کار خطای `AttributeError: 'Environment' object has no attribute 'execute'` را رفع می‌کند.
