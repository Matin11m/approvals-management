# سناریوی تست — Studio Approval Dynamic Routing

## پیش‌نیاز
1. نصب ماژول `studio_approval_dynamic_routing`.
2. باز کردن فرم Rule در Studio Approval.
3. اطمینان از نمایش دو فیلد:
   - `python_code` (Approver Python Routing)
   - `notify_python_code` (Notify Python Routing)

---

## الگوی result در safe_eval (Odoo Python Code / Server Action style)

> در تمام سناریوها خروجی نهایی باید داخل متغیر `result` قرار بگیرد.

```python
# Pattern A: یک کاربر
result = record.user_id

# Pattern B: چند کاربر (recordset)
result = env.ref("stock.group_stock_manager").users

# Pattern C: لیست id
result = [env.user.id]

# Pattern D: خالی (بدون کاربر)
result = []
```

**خروجی‌های معتبر `result`:**
- `res.users` recordset
- `int` (user id)
- `list/tuple/set` از user ids

**خروجی نامعتبر:**
- `True` / `False`
- لیستی که شامل boolean باشد

---

## سناریوها (همه بر اساس الگوی `result`)

### سناریو A — Receipt Approver
**فیلد هدف:** `python_code`
```python
if record.picking_type_id.code == "incoming":
    result = env.ref("stock.group_stock_manager").users[:1]
else:
    result = record.user_id
```
**انتظار:** برای Receipt، approver از مدیر انبار resolve شود.

---

### سناریو B — Delivery Notify
**فیلد هدف:** `notify_python_code`
```python
if record.picking_type_id.code == "outgoing":
    result = env.ref("stock.group_stock_user").users
else:
    result = []
```
**انتظار:** برای Delivery، کاربران گروه انبار نوتیف بگیرند.

---

### سناریو C — Approver by Username
**فیلد هدف:** `python_code`
```python
result = env["res.users"].search([
    ("login", "in", ["warehouse.manager", "stock.supervisor"])
])
```
**انتظار:** فقط کاربران با همین login به‌عنوان approver انتخاب شوند.

---

### سناریو D — Approver by Quantity
**فیلد هدف:** `python_code`
```python
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
if qty >= 100:
    result = env.ref("stock.group_stock_manager").users
else:
    result = record.user_id
```
**انتظار:** برای qty بالا مسیر approval به مدیر انبار منتقل شود.

---

### سناریو E — Notify by Sensitive Product
**فیلد هدف:** `notify_python_code`
```python
has_sensitive_product = any(
    m.product_id.default_code in ["CHEM-001", "FRAGILE-01"]
    for m in record.move_ids_without_package
)
if has_sensitive_product:
    result = env["res.users"].search([
        ("login", "in", ["qa.lead", "qa.user"])
    ])
else:
    result = []
```
**انتظار:** در حضور محصول حساس، فقط QA نوتیف دریافت کند.

---

### سناریو F — Multi-condition Approver
**فیلد هدف:** `python_code`
```python
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
if record.picking_type_id.code == "incoming" and qty >= 50:
    result = env.ref("stock.group_stock_manager").users
elif record.picking_type_id.code == "outgoing" and qty >= 200:
    result = env["res.users"].search([
        ("login", "in", ["warehouse.manager", "ops.manager"])
    ])
else:
    result = record.user_id
```
**انتظار:** خروجی approver بر اساس چند شرط همزمان تعیین شود.

---

### سناریو G — Combined Notify (Group + Username)
**فیلد هدف:** `notify_python_code`
```python
group_users = env.ref("stock.group_stock_user").users
qa_users = env["res.users"].search([
    ("login", "in", ["qa.lead", "qa.user"])
])
result = group_users | qa_users
```
**انتظار:** هر دو مجموعه کاربر نوتیف دریافت کنند.

---

### سناریو H — Fallback Approver
**فیلد هدف:** `python_code`
```python
if record.picking_type_id.code == "internal":
    result = env["res.users"].search([
        ("login", "=", "internal.controller")
    ], limit=1)
else:
    result = record.user_id
```
**انتظار:** در حالت fallback، کاربر پیش‌فرض رکورد approver شود.

---

### سناریو I — SQL Approver
**فیلد هدف:** `python_code`
```python
env.cr.execute("SELECT id FROM res_users WHERE login = %s", ["warehouse.manager"])
row = env.cr.fetchone()
result = [row[0]] if row else []
```
**انتظار:** در صورت وجود کاربر، approver از SQL تعیین شود.

---

### سناریو J — SQL Notify (Multiple Users)
**فیلد هدف:** `notify_python_code`
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
**انتظار:** ۵ کاربر active نوتیف دریافت کنند.

---

## سناریوی اعتبارسنجی خطا

### سناریو K — Boolean Result (نامعتبر)
**فیلد هدف:** `python_code`
```python
result = True
```
**انتظار:** خطای اعتبارسنجی/اجرایی به‌علت نامعتبر بودن نوع خروجی `result`.

### سناریو L — Syntax Error
**فیلد هدف:** `notify_python_code`
```python
if record.picking_type_id.code == "incoming"
    result = env.user
```
**انتظار:** `ValidationError` به‌دلیل syntax نامعتبر.
