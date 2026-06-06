import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent
from telegram import Bot

# 1. إعدادات تليجرام (بياناتك الشخصية مدمجة وجاهزة تماماً)
TELEGRAM_TOKEN = "8287206695:AAG-ddOXd8zPhIHG_ivTx5Iq45zeWoChwD4"
TELEGRAM_CHAT_ID = 8287206695  

# 2. إعدادات تيك توك
# امسح الكلمة بالأسفل واكتب اسم حسابك في تيك توك بين علامتي التنصيص (بدون علامة @)
TIKTOK_USERNAME = "اكتب_اسم_حسابك_هنا"

tg_bot = Bot(token=TELEGRAM_TOKEN)
client = TikTokLiveClient(unique_id=TIKTOK_USERNAME)

# قائمة فحص الرموز والسكريبتات الخبيثة
MALICIOUS_INDICATORS = [
    "http", "www", "://", ".com", ".net", ".xyz", ".ru", ".cc",
    "<script", "javascript", "html", "href", "bot", "crack", 
    "\\", "&&", "$", "{"
]

@client.on("comment")
async def on_comment(event: CommentEvent):
    comment_text = event.comment.lower()
    user_id = event.user.unique_id
    nickname = event.user.nickname

    if any(indicator in comment_text for indicator in MALICIOUS_INDICATORS):
        alert_message = (
            f"🚨 ⚠️ **محاولة هجوم مكتشفة في اللايف!** ⚠️\n\n"
            f"👤 **الحساب المهاجم:** `@{user_id}`\n"
            f"📛 **الاسم المستعار:** {nickname}\n"
            f"💬 **السكريبت/الرابط المرسل:**\n`{event.comment}`\n\n"
            f"🛡️ **إجراء المسؤول:** يرجى حظره فوراً من الهاتف لحماية البث من التقييد!"
        )
        
        try:
            # كتم برمي تلقائي في تيك توك وإرسال إشعار فوري لك على تليجرام
            await event.user.mute(duration=99999)
            await tg_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=alert_message, parse_mode="Markdown")
        except Exception as e:
            fail_message = alert_message + f"\n\n⚠️ تذكير: قم بحظره يدوياً (تعذر الكتم التلقائي)."
            try:
                await tg_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=fail_message, parse_mode="Markdown")
            except Exception as tg_err:
                print(f"فشل إرسال الرسالة إلى تليجرام: {tg_err}")

if __name__ == "__main__":
    print("🛡️ جدار حماية تيك توك السحابي يعمل الآن بنجاح...")
    client.run()
