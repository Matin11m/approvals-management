# سناریوی تست — Studio Approval Dynamic Routing

1. نصب ماژول `studio_approval_dynamic_routing`.
2. باز کردن فرم Rule و بررسی نمایش دو بخش Approver/Notify.
3. ثبت `python_code = result = record.user_id` و بررسی ایجاد request برای approver درست.
4. ثبت `notify_python_code = result = record.team_id.member_ids` و بررسی گیرنده‌های notify.
5. تست syntax نامعتبر و مشاهده ValidationError.
6. تست fallback با خالی‌گذاشتن دو فیلد.


## سناریوهای تست پیشنهادی (کد آماده)

### سناریو A — Operation Type = Receipt
- در `python_code`:
```python
if record.picking_type_id.code == "incoming":
    result = env.ref("stock.group_stock_manager").users[:1]
else:
    result = record.user_id
```
- انتظار: برای Receipt، request برای مدیر انبار ساخته شود.

### سناریو B — Operation Type = Delivery + Notify Team
- در `notify_python_code`:
```python
if record.picking_type_id.code == "outgoing":
    result = env.ref("stock.group_stock_user").users
else:
    result = []
```
- انتظار: در Delivery، کاربران تیم انبار نوتیف بگیرند و به approval session ارجاع شوند.

### سناریو C — بر اساس Username
- در `python_code`:
```python
result = env["res.users"].search([("login", "in", ["warehouse.manager", "stock.supervisor"])])
```
- انتظار: فقط همین یوزرها امکان approve داشته باشند.

### سناریو D — تعداد محصول بالا
- در `python_code`:
```python
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
result = env.ref("stock.group_stock_manager").users if qty >= 100 else record.user_id
```
- انتظار: اگر تعداد >= 100 بود approver به مدیر انبار تغییر کند.

### سناریو E — محصول حساس
- در `notify_python_code`:
```python
has_sensitive_product = any(
    m.product_id.default_code in ["CHEM-001", "FRAGILE-01"]
    for m in record.move_ids_without_package
)
result = env["res.users"].search([("login", "in", ["qa.lead", "qa.user"])]) if has_sensitive_product else []
```
- انتظار: در حضور محصول حساس، کاربران QA نوتیف بگیرند.



### سناریو F — Multi-condition کامل
- در `python_code`:
```python
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
if record.picking_type_id.code == "incoming" and qty >= 50:
    result = env.ref("stock.group_stock_manager").users
elif record.picking_type_id.code == "outgoing" and qty >= 200:
    result = env["res.users"].search([("login", "in", ["warehouse.manager", "ops.manager"])])
else:
    result = record.user_id
```
- انتظار: بر اساس ترکیب operation type و تعداد، approver پویا تعیین شود.

### سناریو G — Notify ترکیبی (گروه + یوزرنیم)
- در `notify_python_code`:
```python
result = env.ref("stock.group_stock_user").users | env["res.users"].search([("login", "in", ["qa.lead", "qa.user"])])
```
- انتظار: هر دو مجموعه کاربر نوتیف دریافت کنند.

### سناریو H — مسیر fallback کامل
- در `python_code`:
```python
if record.picking_type_id.code == "internal":
    result = env["res.users"].search([("login", "=", "internal.controller")], limit=1)
else:
    result = record.user_id
```
- انتظار: در نبود شرط خاص، کاربر پیش‌فرض سند approver باشد.


### سناریو I — Approver با SQL
- در `python_code`:
```python
env.cr.execute("SELECT id FROM res_users WHERE login = %s", ["warehouse.manager"])
row = env.cr.fetchone()
result = [row[0]] if row else []
```
- انتظار: اگر کاربر وجود داشت request برای همان کاربر ساخته شود.

### سناریو J — Notify با SQL + چند کاربر
- در `notify_python_code`:
```python
env.cr.execute("""
    SELECT id
    FROM res_users
    WHERE active = true
    ORDER BY id
    LIMIT 5
""")
result = [row[0] for row in env.cr.fetchall()]
```
- انتظار: ۵ کاربر اول active نوتیف دریافت کنند و وارد session approval شوند.
