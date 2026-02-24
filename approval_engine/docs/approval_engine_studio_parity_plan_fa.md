# نقشه پیاده‌سازی Parity با Odoo Studio Approvals + Python Execute

## هدف
پیاده‌سازی همان تجربه تنظیمات Studio برای Approvals در ماژول `approval_engine`، با یک قابلیت اضافه:
- **Execute Python Code** برای قوانین سفارشی.

---

## 1) آنچه باید با Studio هم‌تراز شود

### 1.1 پارامترهای اصلی Approval Rule
- مدل هدف
- شرط فعال‌سازی
- مرحله‌ها و ترتیب
- تاییدکننده‌ها (user/group)
- رفتار approve/reject
- اعلان‌ها / activity

### 1.2 رفتار UI
- فرم تنظیمات ساده
- ساخت Rule بدون نیاز به کدنویسی (Domain)
- بخش جدا برای «قانون پیشرفته» (Python)

### 1.3 رفتار Runtime
- انتخاب rule مناسب برای رکورد جاری
- اجرای مرحله‌ای تایید
- ثبت لاگ کامل
- اجرای action/hook پس از نتیجه

---

## 2) افزونه موردنیاز شما: Execute Python Code

برای rule engine دو سطح می‌گذاریم:
1. **Domain Rule** (کاربر عادی)
2. **Python Rule** (ادمین فنی)

و برای امنیت:
- استفاده از `safe_eval`
- context محدود (`record`, `env`, `user`, `time`)
- بلاک دسترسی به builtins پرخطر
- لاگ نتیجه اجرا + خطا

---

## 3) پیشنهاد طراحی داده (Data Model)

به مدل template این موارد اضافه/تقویت می‌شود:
- `rule_mode`: `domain | python`
- `rule_domain`
- `rule_python_code`
- `python_timeout_ms` (اختیاری)
- `is_python_enabled`
- `last_eval_status`, `last_eval_message` (برای عیب‌یابی)

---

## 4) ترتیب ارزیابی قوانین
1. اگر `rule_mode=domain`: فقط domain ارزیابی شود.
2. اگر `rule_mode=python`: کد پایتونی اجرا شود و باید bool برگرداند.
3. اگر خطا رخ دهد:
   - خطا لاگ شود
   - رفتار fail-safe (پیشنهادی: عدم match)

---

## 5) طراحی UI پیشنهادی

### بخش Rule
- Rule Type: Domain / Python
- Domain Editor
- Python Editor (multiline + help + examples)
- دکمه Test Rule روی رکورد نمونه

### بخش Safety
- Only Technical Admin can edit python code
- هشدار امنیتی قبل از ذخیره

---

## 6) MVP نزدیک به Studio

### فاز 1 (سریع)
- parity پایه با Studio روی Domain Rule و step approvals
- Python Rule بدون timeout (safe_eval)

### فاز 2
- Test Runner در UI
- Error trace بهتر
- محدودیت‌های امنیتی بیشتر

### فاز 3
- Rule versioning
- Audit کامل تغییرات rule
- Performance optimization/caching

---

## 7) دقیقاً چه چیزی از Studio باید ارسال کنید؟

برای parity دقیق، لطفاً این‌ها را از ماژول Studio/Approvals بفرست:
1. اسکرین‌شات کامل صفحه تنظیمات Approval Rule (همه تب‌ها)
2. خروجی فیلدها/مدل‌های استودیویی مرتبط (technical names)
3. نمونه یک Rule ساده (domain)
4. نمونه یک Rule پیچیده (اگر دارد)
5. رفتار دقیق بعد از approve/reject (actionها)
6. اگر export XML/JSON از Studio داری، همان بهترین ورودی است

با این اطلاعات می‌تونم **یک به یک** همان UX/Behavior را در `approval_engine` replicate کنم.


## محل پیشنهادی قرار دادن فایل‌های Studio در ریپو
- `approval_engine/studio_exports/`
- مثال: `approval_engine/studio_exports/approvals_studio_export_1.xml`
