# سناریوهای تست (Test Scenarios) — Approval Engine

این سند سناریوی تست **ریزبه‌ریز** برای QA/UAT است.

## 0) پیش‌نیاز
- ماژول‌های `approvals` و `approval_engine` نصب باشند.
- کاربر internal داشته باشید.
- یک مدل هدف (مثلاً `purchase.order`) در دسترس باشد.

---

## 1) سناریوی Smoke UI
### Steps
1. وارد اپ شوید.
2. منوهای `Approvals Forms`, `Templates`, `Requests` را باز کنید.
### Expected
- همه منوها دیده شوند.
- صفحات بدون خطا باز شوند.

---

## 2) سناریوی Template فیلدبه‌فیلد
### Steps
1. Template جدید بسازید.
2. فیلدها را تنظیم کنید:
   - Name: `PO Approval`
   - Approvals Form: یک category موجود
   - Model: `purchase.order`
   - Sequence: `10`
   - Active: false (فعلاً)
3. Rule Type را `Domain` بگذارید.
4. Rule Domain: `[('amount_total','>',5000)]`
5. On Approved Method: `action_confirm`
6. On Rejected Method: `button_cancel`
### Expected
- رکورد بدون خطا ذخیره شود.
- فیلدهای rule فقط در mode مربوطه editable/visible باشند.

---

## 3) سناریوی Steps فیلدبه‌فیلد
### Steps
1. در تب Steps یک خط اضافه کنید:
   - Sequence: 10
   - Name: `Manager Approval`
   - Approver Group: گروه مدیر خرید
   - Min Approvals: 1
   - Require All Group Users: false
2. Template را Active کنید.
### Expected
- Active شدن موفق.
- بدون step نتوان Active کرد.

---

## 4) سناریوی Submit
### Steps
1. روی رکورد هدف submit انجام دهید.
2. Request جدید را باز کنید.
### Expected
- State=`waiting`
- Current Step پر شده
- Logs شامل پیام submit باشد (chatter)

---

## 5) سناریوی Approve معمولی
### Steps
1. با کاربر عضو گروه step وارد شوید.
2. Approve بزنید.
### Expected
- Log action=approved ثبت شود.
- اگر step نهایی باشد State=`approved`.

---

## 6) سناریوی Reject معمولی
### Steps
1. Request جدید بسازید و waiting کنید.
2. Reject بزنید.
### Expected
- Log action=rejected ثبت شود.
- State=`rejected`.

---

## 7) سناریوی مجوز (Authorization)
### Steps
1. با کاربر خارج از گروه step Approve/Reject کنید.
### Expected
- خطای عدم مجوز نمایش داده شود.

---

## 8) سناریوی Python Rule — Manual
### Setup Fields
- Python Rule Mode = `manual`
- Python Execute Code:
```python
result = True
message = 'ok'
```
### Steps
1. دکمه `Run Python Rule` را بزنید.
### Expected
- `python_last_result = allowed`
- `python_last_log = ok`

---

## 9) سناریوی Python Rule — Block Approve
### Setup Fields
- Python Rule Mode = `approve`
- Python Execute Code:
```python
result = False
message = 'Approve is blocked by custom rule'
```
### Steps
1. Approve بزنید.
### Expected
- عملیات approve متوقف شود.
- پیام بالا نشان داده شود.
- `python_last_result = blocked`

---

## 10) سناریوی Python Rule — Block Reject
### Setup Fields
- Python Rule Mode = `reject`
- Python Execute Code:
```python
result = False
message = 'Reject is blocked by custom rule'
```
### Steps
1. Reject بزنید.
### Expected
- عملیات reject متوقف شود.
- `python_last_result = blocked`

---

## 11) سناریوی Python Syntax Error
### Setup Fields
- Python Rule Mode = `both`
- Python Execute Code:
```python
if True print('x')
```
### Steps
1. Approve یا Reject بزنید.
### Expected
- خطای اجرای پایتون نمایش داده شود.
- `python_last_result = error`
- `python_last_log` شامل traceback/message خطا.

---

## 12) سناریوی Regression Upgrade
### Steps
1. ماژول را upgrade کنید.
2. مجدد Smoke + Submit + Approve + Python Rule Block را اجرا کنید.
### Expected
- بدون خطای XML/CSV/Model.
- behaviorها پایدار بمانند.
