# مستند جامع Approval Engine (فنی + نحوه استفاده) — Odoo 19

## 1) معرفی
`Approval Engine` یک اپلیکیشن مستقل برای مدیریت تاییدیه‌های سفارشی است که به‌صورت generic روی مدل‌های مختلف Odoo کار می‌کند.

هدف اصلی:
- استفاده از فرم‌های موجود در ماژول `approvals`
- نگاشت آن‌ها به مدل‌های مختلف Odoo
- تعریف مسیر تایید مرحله‌ای با انعطاف بالا

---

## 2) معماری فنی (Technical)

### 2.1 اجزای اصلی
- `approval.engine.template`: قالب تایید
- `approval.engine.step`: مراحل تایید هر قالب
- `approval.engine.binding`: نگاشت UI (view + trigger method)
- `approval.engine.request`: نمونه اجرایی تایید روی یک رکورد واقعی
- `approval.engine.log`: لاگ تصمیمات تایید/رد
- `approval.engine.mixin`: رابط اتصال به هر مدل بیزینسی

### 2.2 وابستگی‌ها
- `base`
- `mail`
- `approvals`

### 2.3 Bootstrap اولیه
در نصب ماژول، sync اولیه از `approval.category` انجام می‌شود تا فرم‌های Approvals به قالب‌های اولیه Engine تبدیل شوند (قابل تکمیل توسط ادمین).

### 2.4 موتور Rule
هر template می‌تواند یک rule داشته باشد:
- `always`
- `domain`
- `python`

### 2.5 State Machine درخواست تایید
`approval.engine.request` در وضعیت‌های زیر حرکت می‌کند:
- `draft` → `waiting` → `approved` یا `rejected`
- و در صورت نیاز `cancelled`

### 2.6 Hookهای بعد از تصمیم
روی template می‌توان تنظیم کرد بعد از تایید/رد نهایی چه متدی روی رکورد مقصد اجرا شود:
- `on_approved_method`
- `on_rejected_method`

---

## 3) نحوه استفاده (User Guide)

### 3.1 اپ کجاست؟
1. Apps → نصب `Approval Engine`
2. از App Launcher وارد `Approval Engine` شوید.
3. منوها:
   - `Approvals Forms`
   - `Templates`
   - `Requests`

### 3.2 سناریوی راه‌اندازی استاندارد

#### گام 1: انتخاب فرم مبدا
از `Approvals Forms` فرم(های) مبدا را بررسی کنید.

#### گام 2: ساخت/ویرایش Template
در `Templates`:
- `Approvals Form` را انتخاب کنید.
- `Model` مقصد را تعیین کنید (مثل `purchase.order`).

#### گام 3: تعریف مراحل تایید
در تب `Steps`:
- مرحله‌ها را با ترتیب مناسب تعریف کنید.
- گروه تاییدکننده و حداقل تعداد تایید را مشخص کنید.

#### گام 4: تعریف اتصال UI
در تب `UI Bindings`:
- `view_id`
- `trigger_method`
- `button_label`

#### گام 5: فعال‌سازی
پس از تکمیل تنظیمات، template را `Active` کنید.

#### گام 6: اجرا
روی رکورد واقعی، متد ارسال برای تایید را اجرا کنید و وضعیت را در `Requests` پیگیری کنید.

---

## 4) مثال سریع (Purchase Order)
1. یک template با مدل `purchase.order` بسازید.
2. یک step برای گروه مدیر خرید اضافه کنید.
3. binding را روی view فرم خرید تنظیم کنید.
4. trigger method را `action_submit_for_approval` بگذارید.
5. template را active کنید.

---

## 5) خطاهای رایج و رفع آن
- **Template فعال بدون Step**
  - حداقل یک Step اضافه کنید.
- **Rule ناقص**
  - اگر type = domain/python است مقدار فیلد rule را کامل کنید.
- **نام متد نامعتبر**
  - نام متد باید identifier معتبر پایتون باشد.

---

## 6) وضعیت فعلی امنیت
در فاز فعلی توسعه، برای قابل استفاده بودن ماژول، یک دسترسی پایه برای کاربران داخلی فعال شده است (بدون تفکیک نقش پیشرفته).

برای production:
- ACL و Record Rule دقیق تعریف شود.
- گروه‌های نقش‌محور نهایی گردد.

---

## 7) مسیر بلوغ بعدی
- Rule Builder گرافیکی
- SLA/Escalation
- نسخه‌بندی Template
- اعمال خودکار Binding روی View (View Injection کنترل‌شده)
- داشبورد KPI تاییدیه‌ها
