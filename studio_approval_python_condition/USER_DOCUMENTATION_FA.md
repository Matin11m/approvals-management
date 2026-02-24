# راهنمای کاربر (فارسی) — شرط پایتون در Studio Approval

## این قابلیت چیست؟
در فرم Rule تایید، علاوه بر Domain می‌توانید یک شرط پایتونی هم بنویسید تا دقیق‌تر مشخص کنید Rule چه زمانی اعمال شود.

## کجا این فیلدها را می‌بینم؟
مسیر: **Studio > Approvals > Rule Form**

بعد از فیلد Domain دو بخش جدید دارید:
1. **Python Guide** (فقط خواندنی)
2. **Python Condition** (قابل ویرایش)

## متغیرهای قابل استفاده در کد
- `env`: محیط Odoo
- `user`: کاربر فعلی
- `record`: رکورد فعلی
- `rule`: Rule فعلی
- `result`: خروجی بولی (باید True/False شود)

## نمونه‌های آماده
```python
result = record.amount_total > 10000
```

```python
result = user.has_group('sales_team.group_sale_manager')
```

```python
result = record.company_id == user.company_id
```

## نکات مهم
- اگر `python_code` خالی باشد، نتیجه پایتون به‌صورت پیش‌فرض True است.
- اگر Domain و Python هر دو پر باشند، **هر دو باید برقرار باشند**.
- در صورت syntax اشتباه، Rule ذخیره نمی‌شود.
- در صورت خطای runtime، پیام خطای کاربرپسند نمایش داده می‌شود.

## روش پیشنهادی استفاده
1. ابتدا Domain را ساده تنظیم کنید.
2. شرط پایتون را کوتاه و شفاف بنویسید.
3. همیشه `result = ...` را صریح ست کنید.
4. قبل از استفاده در Production، سناریوی تست را کامل اجرا کنید.
