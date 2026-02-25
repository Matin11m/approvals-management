# سناریوی تست — Studio Approval Dynamic Routing

1. نصب ماژول `studio_approval_dynamic_routing`.
2. باز کردن فرم Rule و بررسی نمایش دو بخش Approver/Notify.
3. ثبت `python_code = result = record.user_id` و بررسی ایجاد request برای approver درست.
4. ثبت `notify_python_code = result = record.team_id.member_ids` و بررسی گیرنده‌های notify.
5. تست syntax نامعتبر و مشاهده ValidationError.
6. تست fallback با خالی‌گذاشتن دو فیلد.
