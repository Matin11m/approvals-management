# سناریوهای تست کامل Approval Engine (Odoo 19)

این سند یک Test Plan عملی برای بررسی end-to-end ماژول است.

## 1) پیش‌نیازها
- Odoo 19 بالا باشد.
- ماژول‌های `approvals` و `approval_engine` نصب باشند.
- کاربر تست از نوع internal user باشد.

---

## 2) Test Data پیشنهادی
- شرکت: Company A
- کاربران:
  - requester_user (درخواست‌دهنده)
  - approver_1 (عضو گروه مدیر خرید)
  - approver_2 (عضو همان گروه)
- مدل هدف: `purchase.order`
- یک PO تست با مبلغ مشخص (مثلاً 10000)

---

## 3) سناریوی Smoke (نمایش منوها)
### هدف
اطمینان از اینکه منوهای اصلی دیده می‌شوند.

### Steps
1. با کاربر internal وارد شوید.
2. App Launcher → Approval Engine.
3. بررسی منوها:
   - Approvals Forms
   - Templates
   - Requests

### Expected Result
هر سه منو قابل مشاهده و قابل کلیک باشند.

---

## 4) سناریوی Bootstrap Sync از Approvals
### هدف
تایید sync اولیه categoryها به template.

### Steps
1. در `approvals` یک Category بسازید (مثلاً "PO Approval").
2. به `Approval Engine > Templates` بروید.
3. جستجو کنید آیا template متناظر ایجاد شده یا خیر.

### Expected Result
یک template جدید (inactivate) با اتصال به `approval_category_id` موجود باشد.

---

## 5) سناریوی پیکربندی Template
### هدف
تکمیل یک template قابل اجرا.

### Steps
1. یک template باز کنید.
2. Model را روی `purchase.order` بگذارید.
3. Rule Type را `Always` بگذارید.
4. در Steps:
   - Step 1: گروه مدیر خرید، `min_approvals=1`
5. در UI Bindings:
   - view_id از فرم PO
   - trigger_method = `action_submit_for_approval`
   - button_label = `Submit for Approval`
6. template را Active کنید.

### Expected Result
template ذخیره شود و بدون خطای validation فعال شود.

---

## 6) سناریوی ارسال درخواست تایید (Submit)
### هدف
ایجاد request و رفتن به waiting.

### Steps
1. با requester_user یک PO باز کنید.
2. متد submit (از integration) را اجرا کنید.
3. در `Approval Engine > Requests` رکورد جدید را ببینید.

### Expected Result
- request ساخته شود.
- state = `waiting`
- current_step_id روی Step 1 تنظیم شود.

---

## 7) سناریوی Approve مرحله‌ای
### هدف
تکمیل فرآیند تایید.

### Steps
1. با approver_1 وارد شوید.
2. request را باز کنید.
3. روی Approve بزنید.

### Expected Result
- log با action=`approved` ثبت شود.
- اگر مرحله آخر است state=`approved` شود.
- اگر hook تایید تعریف شده، متد مربوط روی رکورد مقصد اجرا شود.

---

## 8) سناریوی Reject
### هدف
بررسی رد درخواست و ثبت لاگ.

### Steps
1. یک request جدید به waiting ببرید.
2. با approver مجاز روی Reject بزنید.

### Expected Result
- state=`rejected`
- log با action=`rejected` ثبت شود.
- hook رد (در صورت تعریف) اجرا شود.

---

## 9) سناریوی مجوز تاییدکننده
### هدف
جلوگیری از approve توسط کاربر غیرمجاز.

### Steps
1. کاربری خارج از گروه step وارد شود.
2. روی Approve/Reject تلاش کند.

### Expected Result
سیستم باید خطای دسترسی تابعی برگرداند (عدم مجاز بودن).

---

## 10) سناریوی Rule: Domain
### هدف
اعمال template شرطی.

### Steps
1. Rule Type = Domain
2. rule_domain مثال: `[('amount_total','>',5000)]`
3. دو PO بسازید: یکی 3000 و دیگری 10000
4. submit را روی هر دو تست کنید.

### Expected Result
template فقط برای رکوردهای match شده اعمال شود.

---

## 11) سناریوی Rule: Python
### هدف
صحت ارزیابی python rule.

### Steps
1. Rule Type = Python
2. rule_python مثال: `record.amount_total > 5000 and user.has_group('purchase.group_purchase_manager')`
3. submit را با کاربران مختلف تست کنید.

### Expected Result
فقط در شرایط True template انتخاب شود.

---

## 12) سناریوی Data Integrity
### مواردی که باید تست شوند
- Template active بدون step نباید ذخیره/فعال شود.
- نام method نامعتبر نباید پذیرفته شود.
- trigger_method نامعتبر در binding نباید پذیرفته شود.
- min_approvals کمتر از 1 نباید پذیرفته شود.

---

## 13) سناریوی Regression بعد از Upgrade
### Steps
1. ماژول را upgrade کنید.
2. منوها و دسترسی پایه را چک کنید.
3. یک request جدید end-to-end اجرا کنید.

### Expected Result
بدون خطای XML/CSV/Model، سیستم قابل استفاده بماند.

---

## 14) چک‌لیست نهایی پذیرش (UAT)
- [ ] منوهای اصلی دیده می‌شوند.
- [ ] فرم‌های approvals قابل مشاهده‌اند.
- [ ] template قابل ساخت و فعال‌سازی است.
- [ ] submit / approve / reject صحیح کار می‌کند.
- [ ] لاگ تصمیم‌ها ثبت می‌شود.
- [ ] ruleهای domain/python طبق انتظار عمل می‌کنند.
- [ ] خطاهای validation درست نمایش داده می‌شود.
