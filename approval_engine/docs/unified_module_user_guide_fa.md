# راهنمای کاربر (User Guide) — Approval Engine

این راهنما کاملاً عملیاتی است و **فیلد به فیلد** بخش‌های اصلی را توضیح می‌دهد.

## 1) نصب و ورود
1. از Apps، ماژول `Approval Engine` را نصب کنید.
2. وارد اپ شوید.
3. منوهای اصلی:
   - `Approvals Forms`
   - `Templates`
   - `Requests`

---

## 2) فرم Templates — توضیح فیلد به فیلد

### بخش اصلی
- **Name**: نام قالب (مثلاً PO Approval High Amount).
- **Approvals Form**: فرم مبدا از ماژول approvals.
- **Model**: مدل هدف (مثلاً `purchase.order`).
- **Company**: شرکت مالک قالب.
- **Sequence**: اولویت اعمال؛ عدد کمتر اولویت بالاتر.
- **Active**: فعال‌سازی قالب برای استفاده runtime.

### بخش Rule
- **Rule Type**:
  - `Always`: همیشه اعمال شود.
  - `Domain`: اعمال بر اساس فیلتر دامنه.
  - `Python Expression`: اعمال با عبارت پایتونی.
- **Rule Domain** (فقط برای Domain):
  - مثال: `[('amount_total','>',5000)]`
- **Rule Python** (فقط برای Python Expression):
  - باید True/False برگرداند.
- **On Approved Method**:
  - متد رکورد هدف پس از تایید نهایی (مثلاً `action_confirm`).
- **On Rejected Method**:
  - متد رکورد هدف پس از رد (مثلاً `action_cancel`).

### تب Steps
هر خط یک مرحله:
- **Sequence**: ترتیب مرحله.
- **Name**: عنوان مرحله.
- **Approver Group**: گروه مجاز برای تایید.
- **Min Approvals**: حداقل تعداد تایید.
- **Require All Group Users**: اگر فعال باشد، همه اعضا باید تایید کنند.

### تب UI Bindings
- **Sequence**: ترتیب binding.
- **View**: ویوی هدف (از همان model).
- **Trigger Method**: متدی که submit را شروع می‌کند.
- **Button Label**: متن نمایشی دکمه (metadata).

### تب Description
- توضیحات داخلی فرآیند.

---

## 3) فرم Requests — توضیح فیلد به فیلد

### Header Buttons
- **Submit**: ارسال برای تایید (از draft/cancelled).
- **Approve**: تایید مرحله جاری.
- **Reject**: رد مرحله جاری.
- **Cancel**: لغو درخواست.
- **Run Python Rule**: اجرای دستی Rule (فقط در mode=manual).

### فیلدهای اصلی
- **Name**: شماره request.
- **Template**: قالب مرتبط.
- **Requester**: ایجادکننده request.
- **Company**: شرکت.
- **Res Model / Res ID / Reference**: رکورد هدف.
- **Current Step**: مرحله جاری.
- **State**: وضعیت چرخه.

### تب Logs
- **Create Date**: زمان ثبت تصمیم.
- **Step**: مرحله.
- **User**: تصمیم‌گیرنده.
- **Action**: approved یا rejected.
- **Comment**: توضیح ثبت‌شده.

### تب Python Rules
- **Python Rule Mode**:
  - `none`: غیرفعال
  - `manual`: فقط دستی
  - `approve`: قبل از approve
  - `reject`: قبل از reject
  - `both`: قبل از approve و reject
- **Python Execute Code**: کد قابل اجرا.
- **Python Last Result**: allowed / blocked / error.
- **Python Last Log**: پیام/خطای آخر اجرا.

---

## 4) مثال‌های آماده برای Python Execute Code

### مثال 1: بلاک تایید برای مبلغ بالا
```python
if record and record.amount_total > 10000:
    result = False
    message = 'Amount is over allowed threshold.'
```

### مثال 2: فقط مدیر خرید مجاز به تایید
```python
if action == 'approve' and not user.has_group('purchase.group_purchase_manager'):
    result = False
    message = 'Only Purchase Manager can approve this request.'
```

### مثال 3: لاجیک ترکیبی
```python
if record and record.company_id and record.company_id.name != 'Company A':
    result = False
    message = 'Approval is restricted to Company A records.'
```

---

## 5) خطاهای رایج
- قالب active بدون step -> ذخیره/فعال‌سازی رد می‌شود.
- کاربر خارج از گروه مرحله -> approve/reject خطا می‌دهد.
- syntax error در python code -> `python_last_result=error`.
- `result=False` -> اکشن بلاک و پیام کاربر نمایش داده می‌شود.
