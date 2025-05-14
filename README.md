# GPT GitHub Proxy

مشروع Flask صغير يسمح لنموذج GPT بإرسال أوامر يتم تنفيذها عبر GitHub، واسترجاع البيانات وتحليلها تلقائيًا.

## الوظائف المدعومة
- جلب آخر الكوميتات من مستودع GitHub
- تحليلها باستخدام GPT-4 من OpenAI

## كيف يعمل؟
1. أرسل أمرًا إلى `/run-action` يتضمن نوع الإجراء (مثلاً: `fetch_commits`)
2. يتصل Flask بـ GitHub API
3. يحلل البيانات باستخدام OpenAI
4. يرجع لك النتيجة كـ JSON

## المصادقة
يجب تمرير `x-api-key` في Header من أجل الوصول إلى الوسيط.

## تشغيل محلي:
```bash
pip install -r requirements.txt
python app.py
```

## نشر تلقائي
ارفع المشروع على GitHub، ثم انشره مجانًا عبر [https://render.com](https://render.com)
