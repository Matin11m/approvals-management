# راهنمای کاربر — Studio Approval Dynamic Routing

در فرم Rule بعد از `domain` دو بخش دارید:
- Approver Python Routing
- Notify Python Routing

در هر بخش:
- راهنمای readonly قوانین
- راهنمای readonly مثال‌ها
- textbox برای کد

نمونه‌ها:
```python
result = record.user_id
```

```python
result = record.team_id.member_ids
```


## سناریوهای آماده برای تست (انبار)

> نکته: در تمام مثال‌ها باید خروجی نهایی در متغیر `result` قرار بگیرد.

### 1) Approver بر اساس Operation Type
```python
# اگر عملیات Receipt باشد مدیر انبار تایید کند
if record.picking_type_id.code == "incoming":
    result = env.ref("stock.group_stock_manager").users[:1]
# اگر عملیات Delivery باشد مسئول خروجی تایید کند
elif record.picking_type_id.code == "outgoing":
    result = env["res.users"].search([("login", "=", "out_user")], limit=1)
# در سایر حالت‌ها خود کاربر سند
else:
    result = record.user_id
```

### 2) Approver بر اساس نام کاربری (username/login)
```python
# لیست لاگین‌های مجاز برای تایید
allowed_logins = ["warehouse.manager", "stock.supervisor"]
result = env["res.users"].search([("login", "in", allowed_logins)])
```

### 3) Approver بر اساس تعداد محصول/حجم انتقال
```python
# اگر تعداد کل آیتم‌ها زیاد بود، مدیر تایید کند
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
if qty >= 100:
    result = env.ref("stock.group_stock_manager").users
else:
    result = record.user_id
```

### 4) Notify بر اساس Operation Type
```python
# برای Delivery به تیم انبار نوتیف بده
if record.picking_type_id.code == "outgoing":
    result = env.ref("stock.group_stock_user").users
else:
    result = []
```

### 5) Notify بر اساس محصول خاص
```python
# اگر محصولی با کد خاص در انتقال بود به QA نوتیف بده
has_sensitive_product = any(
    m.product_id.default_code in ["CHEM-001", "FRAGILE-01"]
    for m in record.move_ids_without_package
)
if has_sensitive_product:
    result = env["res.users"].search([("login", "in", ["qa.lead", "qa.user"])])
else:
    result = []
```

### 6) Notify/Approve برای انتقال‌های با ارزش بالا
```python
# مجموع ارزش تقریبی انتقال
amount = sum(
    m.product_uom_qty * (m.product_id.standard_price or 0.0)
    for m in record.move_ids_without_package
)
if amount >= 50000000:
    # هم درخواست قابل Approve برای مدیر مالی/انبار ساخته می‌شود
    # هم نوتیف برای همین کاربران ارسال می‌شود (در صورت استفاده در notify_python_code)
    result = env["res.users"].search([("login", "in", ["finance.manager", "warehouse.manager"])])
else:
    result = record.user_id
```


## مرجع کامل برای رسیدن به Approver با کد پایتون

### آبجکت‌هایی که داخل کد دارید
- `env`: دسترسی کامل به مدل‌ها (`env["res.users"]`, `env["stock.picking"]`, ...)
- `user`: کاربر جاری
- `record`: رکوردی که approval روی آن انجام می‌شود (مثلاً `stock.picking`)
- `rule`: قانون approval جاری
- `result`: خروجی نهایی که **باید** کاربران را برگرداند

### نوع خروجی معتبر برای `result`
- `res.users` recordset
- یک شناسه کاربر (`int`)
- لیست/tuple/set از شناسه کاربران

### الگوهای پایه برای پیدا کردن کاربران
```python
# 1) بر اساس لاگین
result = env["res.users"].search([("login", "=", "warehouse.manager")], limit=1)

# 2) بر اساس گروه
result = env.ref("stock.group_stock_manager").users

# 3) از روی فیلدهای خود رکورد
result = record.user_id

# 4) ترکیب چند منبع کاربر
u1 = env.ref("stock.group_stock_manager").users
u2 = env["res.users"].search([("login", "in", ["qa.lead", "qa.user"])])
result = u1 | u2
```

### الگوی چندشرطی (Multi-condition)
```python
if record.picking_type_id.code == "incoming" and record.company_id.id == 1:
    result = env.ref("stock.group_stock_manager").users
elif record.picking_type_id.code == "outgoing" and record.priority == "1":
    result = env["res.users"].search([("login", "in", ["warehouse.manager", "stock.supervisor"])])
elif sum(record.move_ids_without_package.mapped("product_uom_qty")) >= 100:
    result = env["res.users"].search([("login", "=", "ops.manager")], limit=1)
else:
    result = record.user_id
```

### سناریوهای تکمیلی برای انبار

#### 7) شرط همزمان Operation Type + تعداد محصول + نام کاربر
```python
qty = sum(record.move_ids_without_package.mapped("product_uom_qty"))
if record.picking_type_id.code == "outgoing" and qty >= 200:
    result = env["res.users"].search([("login", "in", ["warehouse.manager", "ops.manager"])])
elif record.picking_type_id.code == "incoming":
    result = env.ref("stock.group_stock_manager").users
else:
    result = env["res.users"].search([("login", "=", "stock.supervisor")], limit=1)
```

#### 8) شرط بر اساس مقصد/مبدا انبار
```python
if record.location_dest_id.usage == "internal":
    result = env["res.users"].search([("login", "=", "internal.controller")], limit=1)
elif record.location_id.usage == "supplier":
    result = env.ref("stock.group_stock_manager").users
else:
    result = record.user_id
```

#### 9) Notify برای چند گروه همزمان
```python
stock_users = env.ref("stock.group_stock_user").users
stock_managers = env.ref("stock.group_stock_manager").users
qa_users = env["res.users"].search([("login", "in", ["qa.lead", "qa.user"])])
result = stock_users | stock_managers | qa_users
```

#### 10) Notify فقط در حالت Backorder
```python
# اگر رکوردهای move خطی با qty_done کمتر از تقاضا داشته باشند
has_partial = any(m.quantity < m.product_uom_qty for m in record.move_ids_without_package)
if has_partial:
    result = env["res.users"].search([("login", "in", ["warehouse.manager", "planning.user"])])
else:
    result = []
```

### نکات مهم
- حتماً در همه مسیرها (`if/elif/else`) مقدار `result` را ست کنید.
- از برگرداندن مقدار `True/False` خودداری کنید.
- برای debug سریع، از شرط‌های ساده شروع کنید و مرحله‌ای پیچیده‌ترش کنید.


### الگوی SQL برای پیدا کردن Approver/Notify
> بله، می‌توانید با `env.cr` کوئری SQL بزنید و خروجی را به `result` تبدیل کنید.
> خروجی SQL را به یکی از فرمت‌های معتبر تبدیل کنید (لیست id یا `res.users`).

```python
# Approver با SQL
env.cr.execute("""
    SELECT id
    FROM res_users
    WHERE active = true
      AND login IN %s
""", [("warehouse.manager", "stock.supervisor")])
user_ids = [row[0] for row in env.cr.fetchall()]
result = user_ids
```

```python
# Notify با SQL بر اساس گروه انبار
env.cr.execute("""
    SELECT ru.id
    FROM res_users ru
    JOIN res_groups_users_rel rel ON rel.uid = ru.id
    JOIN ir_model_data imd ON imd.res_id = rel.gid
    JOIN ir_module_module mod ON mod.name = imd.module
    WHERE imd.model = 'res.groups'
      AND imd.name = 'group_stock_user'
      AND mod.state = 'installed'
""")
result = [row[0] for row in env.cr.fetchall()]
```

```python
# ترکیب SQL + ORM
env.cr.execute("SELECT id FROM res_users WHERE login = %s", ["qa.lead"])
sql_ids = [r[0] for r in env.cr.fetchall()]
orm_users = env.ref("stock.group_stock_manager").users
result = env["res.users"].browse(sql_ids) | orm_users
```

### نکات ایمنی SQL
- فقط `SELECT` بزنید (برای این use-case نیازی به INSERT/UPDATE/DELETE نیست).
- حتماً از پارامترگذاری استفاده کنید (`%s`) و رشته را مستقیم concat نکنید.
- اگر رکوردی پیدا نشد، `result = []` بدهید تا خطای type نگیرید.
