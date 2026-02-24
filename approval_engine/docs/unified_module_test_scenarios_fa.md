# سناریوهای تست (Test Scenarios) — Approval Engine

## A) Smoke
1. نصب ماژول
2. مشاهده منوهای اصلی
3. باز شدن صفحات Templates/Requests

## B) Template + Step
1. ساخت Template
2. اضافه کردن Step
3. فعال‌سازی Template
**Expected:** بدون خطا ذخیره شود.

## C) Submit Flow
1. ایجاد رکورد هدف
2. submit for approval
**Expected:**
- request ایجاد شود
- state=`waiting`
- current_step پر شود

## D) Approve Flow
1. approver مجاز approve کند
**Expected:**
- log approve ثبت شود
- اگر آخرین step بود state=`approved`

## E) Reject Flow
1. approver مجاز reject کند
**Expected:**
- log reject ثبت شود
- state=`rejected`

## F) Authorization
1. کاربر غیرمجاز approve/reject کند
**Expected:** خطای عدم مجوز

## G) Python Rule - Manual
1. mode=`manual`
2. code با `result=True`
3. Run Python Rule
**Expected:** `python_last_result=allowed`

## H) Python Rule - Block Approve
1. mode=`approve`
2. code: `result=False`
3. Approve
**Expected:** approve بلاک شود + پیام خطا

## I) Python Rule - Block Reject
1. mode=`reject`
2. code: `result=False`
3. Reject
**Expected:** reject بلاک شود

## J) Regression after upgrade
1. upgrade module
2. بازبینی منوها و request flow
3. اجرای یک سناریوی Python Rule
**Expected:** بدون خطای XML/Model/CSV
