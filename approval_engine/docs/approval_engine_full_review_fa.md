# بررسی کامل وضعیت فعلی Approval Engine و اقدامات پیشنهادی

## جمع‌بندی سریع
وضعیت فعلی ماژول برای فاز MVP **قابل استفاده** است، اما برای parity کامل با Studio Approvals هنوز چند گپ مهم داریم.

---

## 1) چیزهایی که الان درست کار می‌کند
1. ماژول به‌صورت App نصب می‌شود.
2. منوهای اصلی (`Approvals Forms`, `Templates`, `Requests`) نمایش داده می‌شوند.
3. ساخت Template و Step انجام می‌شود.
4. Ruleهای `always/domain/python` در هسته وجود دارند.
5. Request lifecycle (`draft/waiting/approved/rejected/cancelled`) پیاده است.
6. مستندات فنی/کاربری/تست داخل خود ماژول قرار گرفته‌اند.

---

## 2) گپ‌های اصلی تا parity با Studio

### 2.1) UI Binding هنوز اجرایی کامل نیست
- الان `approval.engine.binding` صرفاً داده نگه می‌دارد.
- تزریق خودکار دکمه/اکشن در view هدف هنوز پیاده نشده.

**اثر:** کاربر binding تعریف می‌کند ولی بدون integration در مدل/ویو، رفتار کامل Studio را نمی‌بیند.

### 2.2) Python Rule نیاز به Hardening دارد
- `safe_eval` استفاده شده اما:
  - sandbox policy دقیق‌تر لازم است.
  - error telemetry و debug trace استاندارد لازم است.
  - test-runner برای rule در UI نداریم.

### 2.3) parity دقیق Studio نیازمند ورودی واقعی Studio است
برای تطابق 1:1 باید artifactهای واقعی Studio (XML/JSON/field map/screens) بررسی شوند.

---

## 3) اگر همین الان بخواهیم به parity نزدیک شویم (پیشنهاد عملی)

### فاز A (سریع و کم‌ریسک)
1. اضافه کردن Wizard «Test Rule» برای ارزیابی domain/python روی رکورد نمونه.
2. ثبت `last_eval_status/last_eval_message` روی template.
3. نمایش پیام خطای قابل فهم در UI.

### فاز B (Parity کاربردی)
1. ایجاد integration action استاندارد برای model هدف:
   - دکمه `Submit for Approval`
   - open requests smart button
2. اتصال binding به اکشن واقعی (نه فقط metadata).

### فاز C (Parity پیشرفته)
1. Rule builder گرافیکی مشابه Studio.
2. delegation/escalation.
3. versioning rule/template.

---

## 4) درباره دو فایل Studio که گفتی
اگر این دو فایل واقعاً شامل تنظیمات Studio Approvals هستند، من می‌تونم دقیقاً انجام بدهم:
1. استخراج مدل‌ها/فیلدها/rule settings
2. mapping 1:1 به `approval.engine.template/step/binding`
3. ساخت migration/import utility
4. تولید گزارش اختلاف (Diff Report)

### محل پیشنهادی قرار دادن فایل‌ها در ریپو
- `approval_engine/studio_exports/<file1>.xml`
- `approval_engine/studio_exports/<file2>.xml`

---

## 5) خروجی قابل تحویل بعد از دریافت فایل‌های Studio
- `studio_mapping_report.md`: نگاشت کامل Studio -> Approval Engine
- `studio_importer.py` یا server action import utility
- patch کد برای parity behavior در runtime
- سناریوی تست parity اختصاصی بر اساس همان تنظیمات واقعی شما

---

## 6) نتیجه نهایی این بررسی
- ماژول الان برای MVP قابل استفاده است.
- برای parity واقعی Studio، **اقدام بعدی حیاتی** تحلیل فایل‌های export Studio شماست.
- بلافاصله بعد از دریافت آن‌ها می‌توانم فاز import/mapping را پیاده‌سازی کنم.
