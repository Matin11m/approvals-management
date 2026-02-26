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
