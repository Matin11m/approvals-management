# سناریوهای تست ماژول یکپارچه Approval Engine

## سناریو 1: ایجاد Template و Step
- Template ایجاد شود.
- حداقل یک Step ثبت شود.
- Template فعال شود.

## سناریو 2: Submit Request
- درخواست ایجاد شود.
- state به `waiting` برود.

## سناریو 3: Python Rule دستی
- mode=`manual`
- Run Python Rule
- نتیجه در `python_last_result` ثبت شود.

## سناریو 4: بلاک Approve با Python
- mode=`approve`
- کد: `result=False`
- انتظار: approve متوقف شود.

## سناریو 5: بلاک Reject با Python
- mode=`reject`
- کد: `result=False`
- انتظار: reject متوقف شود.

## سناریو 6: اجرای موفق
- mode=`both`
- کد: `result=True`
- انتظار: approve/reject طبق روال عادی اجرا شود.
