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
