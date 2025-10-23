# YouTube Shorts → Telegram (Cat/Meow) Bot

این پروژه یک ربات ساده‌ست که هر روز **ساعت 12:00 به‌وقت Europe/Amsterdam** ویدیوهای جدید YouTube Shorts شامل یکی از کلمات `cat`, `meow`, `گربه`, `میو` را بررسی می‌کند، و اگر هر ویدیو **بیش از 200,000 لایک** داشت، ویدیو را به‌صورت فایل MP4 دانلود کرده و به چت خصوصی تلگرام ارسال می‌کند.

## چه کارهایی انجام می‌دهد
- جست‌وجوی ویدیوهای منتشرشده در ۲۴ ساعت اخیر با عباراتِ مشخص
- بررسی تعداد لایک‌ها (فقط ویدیوهایی با لایک >= 200,000)
- دانلود ویدیو با `yt-dlp` و ارسال فایل MP4 به تلگرام
- جلوگیری از ارسال تکراری با ذخیره شناسه ویدیوها در `sent_videos.json`
- هر روز به‌صورت خودکار از طریق GitHub Actions اجرا می‌شود

## تنظیمات (GitHub Secrets)
در مخزن GitHub خود این Secrets را بسازید:
- `YT_API_KEY` — API Key از Google (YouTube Data API v3)
- `TELEGRAM_BOT_TOKEN` — توکن ربات تلگرام (BotFather)
- `TELEGRAM_CHAT_ID` — شناسه numeric چت خصوصی یا user id
- (اختیاری) `LIKE_THRESHOLD` — مقدار آستانه لایک (پیش‌فرض 200000)

## نکات مهم
- زمان‌بندی workflow اکنون روی `'0 11 * * *'` تنظیم شده (یعنی 11:00 UTC — معادل 12:00 CET). اگر می‌خواهید زمان دیگری باشد، فایل `.github/workflows/schedule.yml` را تغییر دهید.
- از آنجا که ربات ویدیوها را به‌عنوان فایل ارسال می‌کند، ممکن است حجم و پهنای باند بالایی مصرف شود. مراقب محدودیت‌های GitHub Actions و نرخ ارسال به تلگرام باشید.
- ذخیره‌ی ویدیوها در پوشه‌ی `downloads/` انجام می‌شود؛ اگر فضای ذخیره می‌شود، بهتر است پاک‌سازی دوره‌ای اضافه کنید.

## اجرای محلی (برای تست)
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export YT_API_KEY="..."
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
python bot.py
```

