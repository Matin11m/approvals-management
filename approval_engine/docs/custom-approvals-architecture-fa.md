# راهکار ارجاع فرم‌های سفارشی Approvals در Odoo 19

این سند یک الگوی عملی برای زمانی است که در ماژول `approvals` فرم‌ها/فیلدها و منطق اختصاصی ساخته‌اید و می‌خواهید همان فرم‌ها از ماژول‌های دیگر (Purchase, HR, Accounting, Project, …) قابل ارجاع و استفاده باشند.

## 1) گزینه‌های قابل اجرا

### گزینه A) توسعه‌ی مستقیم approvals + اکشن‌های سفارشی
- روی مدل‌های موجود `approval.request` و `approval.category` فیلدهای اختصاصی اضافه می‌کنید.
- برای هر ماژول مقصد (مثلاً `purchase.order`) یک دکمه «ارسال برای تایید» می‌گذارید.
- با `context` و فیلد `res_model`/`res_id` (یا معادل سفارشی) رکورد مبدا را به درخواست تایید لینک می‌کنید.

**مزیت:** سریع و کم‌هزینه برای شروع.
**ضعف:** وقتی سناریوها زیاد می‌شوند، نگهداری سخت می‌شود و منطق پراکنده خواهد شد.

### گزینه B) ماژول واسط برای هر دامنه (Connector Modules)
- یک هسته approvals دارید.
- برای هر دامنه یک ماژول اتصال می‌سازید:
  - `approvals_purchase_connector`
  - `approvals_hr_connector`
  - `approvals_account_connector`
- هر Connector فقط mapping فیلدها، rule و buttonهای همان دامنه را نگه می‌دارد.

**مزیت:** ساختار تمیز، قابل تست، مناسب تیمی.
**ضعف:** تعداد ماژول‌ها بیشتر می‌شود.

### گزینه C) طراحی یک «Approval Engine» جامع (پیشنهادی)
- یک ماژول مرکزی بسازید که approvals را به صورت Generic مدیریت کند.
- ارجاع به هر مدل با پیکربندی انجام شود (بدون کدنویسی زیاد برای هر سناریو).

**مزیت:** بیشترین انعطاف و مقیاس‌پذیری.
**ضعف:** پیاده‌سازی اولیه پیچیده‌تر است.

---

## 2) آیا می‌شود یک ماژول جامع نوشت؟

بله، کاملاً. و برای نیاز شما معمولاً بهترین مسیر همین است.

### اجزای پیشنهادی ماژول جامع

1. **Approval Template**
   - تعیین می‌کند این قالب برای چه `model`ی است.
   - شامل مرحله‌ها، ترتیب‌ها، شروط، SLA و دسترسی‌ها.

2. **Approval Stage/Step**
   - هر مرحله: چه گروه/کاربری تایید کند.
   - نوع rule: `any`, `all`, `minimum_count`.

3. **Approval Rule (Domain-based)**
   - شرط فعال شدن قالب با domain یا Python safe eval (با احتیاط).
   - مثال: اگر مبلغ PO > 500M، مرحله CFO اضافه شود.

4. **Approval Instance/Request**
   - نمونه‌ی اجرایی روی یک رکورد واقعی (`res_model`, `res_id`).
   - وضعیت‌های استاندارد: draft, waiting, approved, rejected, canceled.

5. **Field Mapping Layer**
   - تعریف اینکه چه فیلدهایی از مدل مبدا روی فرم تایید نمایش داده/کپی شوند.
   - پشتیبانی از required/readonly/visibility شرطی.

6. **Action Hooks**
   - قبل از ارسال، بعد از تایید، بعد از رد.
   - مثلا بعد از تایید نهایی: confirm سفارش خرید.

7. **Security Matrix**
   - ACL + Record Rules + گروه‌های نقش‌محور.
   - جلوگیری از bypass تایید با write مستقیم.

8. **Audit & Traceability**
   - ثبت کامل log: چه کسی، چه زمانی، چه تصمیمی.
   - نگهداری attachmentها و chatter برای ممیزی.

---

## 3) الگوی فنی پیشنهادی برای Odoo 19

- هسته را در یک ماژول مثل `x_approval_engine` نگه دارید.
- برای هر دامنه فقط plugin/connector کوچک بسازید.
- از delegation/inheritance استاندارد Odoo استفاده کنید (`_inherit`, mixin).
- منطق تصمیم‌گیری را از view جدا کنید (service-like methods در model).
- از `mail.thread` و `activity` برای اعلان، escalation و reminder استفاده کنید.
- برای performance:
  - index روی فیلدهای جست‌وجو (`state`, `res_model`, `res_id`, `company_id`).
  - prefetch مناسب و جلوگیری از loopهای سنگین compute.

---

## 4) مسیر اجرایی مرحله‌به‌مرحله

1. **ثابت‌سازی مدل داده**
   - `approval.template`, `approval.step`, `approval.request`, `approval.log`.

2. **ساخت API داخلی یکنواخت**
   - `action_submit_for_approval(record)`
   - `action_approve(step)`
   - `action_reject(reason)`

3. **اتصال اولین دامنه (Pilot)**
   - مثلاً Purchase را کامل کنید و edge caseها را ببندید.

4. **ساخت Rule Builder در UI**
   - مدیر سیستم بتواند بدون کدنویسی قالب/مرحله بسازد.

5. **گسترش به دامنه‌های دیگر با Connector**
   - HR / Expense / Accounting.

6. **گزارش و KPI**
   - زمان میانگین تایید، bottleneck مراحل، نسبت رد.

---

## 5) نکات مهم که معمولاً فراموش می‌شوند

- **چندشرکتی (Multi-company):** ruleها و داده‌ها company-aware باشند.
- **Versioning قالب:** تغییر قالب روی درخواست‌های قبلی اثر نگذارد.
- **Delegation/Proxy approval:** جانشین تاییدکننده.
- **Escalation خودکار:** با cron/job اگر SLA رد شد.
- **قابلیت override کنترل‌شده:** با سطح دسترسی خاص + log اجباری.

---

## 6) جمع‌بندی تصمیم

اگر الان فرم و منطق سفارشی ساخته‌اید و می‌خواهید در بخش‌های مختلف سیستم reuse شود:
- کوتاه‌مدت: با Connector برای ماژول‌های کلیدی شروع کنید.
- میان‌مدت/بلندمدت: یک `Approval Engine` جامع و پیکربندی‌محور بسازید.

این ترکیب هم سریع شما را جلو می‌برد، هم در آینده نگهداری سیستم را ساده می‌کند.
