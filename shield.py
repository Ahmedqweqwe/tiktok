import asyncio
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent
from telegram import Bot

# 1. إعدادات تليجرام الأساسية (التوكن والـ ID الخاص بك جاهزان)
TELEGRAM_TOKEN = "8287206695:AAG-ddOXd8zPhIHG_ivTx5Iq45zeWoChwD4"
tg_bot = Bot(token=TELEGRAM_TOKEN)

# رقم الـ ID الشخصي الخاص بك (المسؤول) المأخوذ من صورتك
ADMIN_CHAT_ID = 7896705259  

# 2. 🛡️ قائمة الحماية المشتركة (جدول الأصدقاء واللايفات) 🛡️
PROTECTED_USERS = {
    "حسابك_أنت_في_تيك_توك": ADMIN_CHAT_ID,        # ضع اسم حسابك في تيك توك
    "roch.roch765": 123456789,                  # ضع رقم الـ ID الخاص بصديقك على تليجرام هنا
}

# قائمة فحص الرموز والسكريبتات الخبيثة في التعليقات
MALICIOUS_INDICATORS = [
    "http", "www", "://", ".com", ".net", ".xyz", ".ru", ".cc",
    "<script", "javascript", "html", "href", "bot", "crack", 
    "\\", "&&", "$", "{"
]

async def start_protection_for_user(tiktok_username, telegram_id):
    client = TikTokLiveClient(unique_id=tiktok_username)
    print(f"🛡️ جدار الحماية بدأ بمراقبة لايف الحساب: @{tiktok_username}")

    @client.on("comment")
    async def on_comment(event: CommentEvent):
        comment_text = event.comment.lower()
        attacker_id = event.user.unique_id
        nickname = event.user.nickname

        if any(indicator in comment_text for indicator in MALICIOUS_INDICATORS):
            alert_message = (
                f"🚨 ⚠️ **محاولة هجوم مكتشفة!** ⚠️\n\n"
                f"📺 **اللايف المستهدف:** `@{tiktok_username}`\n"
                f"👤 **الحساب المهاجم:** `@{attacker_id}`\n"
                f"📛 **الاسم المستعار:** {nickname}\n"
                f"💬 **السكريبت/الرابط المرسل:**\n`{event.comment}`\n\n"
                f"🛠️ **إجراء المسؤول:** يرجى حظره فوراً لحماية البث من التقييد!"
            )
            
            try:
                # محاولة كتم المهاجم في تيك توك تلقائياً
                await event.user.mute(duration=99999)
            except Exception as e:
                print(f"تعذر الكتم التلقائي في لايف @{tiktok_username}: {e}")

            # إرسال البلاغ لك (المسؤول) دائماً
            try:
                await tg_bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_message, parse_mode="Markdown")
            except: pass

            # إرسال البلاغ للصديق صاحب اللايف أيضاً إذا كان حسابه مختلفاً عن حسابك
            if telegram_id != ADMIN_CHAT_ID:
                try:
                    await tg_bot.send_message(chat_id=telegram_id, text=alert_message, parse_mode="Markdown")
                except: pass

    try:
        await client.start()
    except Exception as err:
        print(f"❌ تعذر الاتصال بـ لايف @{tiktok_username} (قد يكون مغلقاً حالياً): {err}")

async def main():
    print("🚀 جدار الحماية السحابي المشترك يعمل الآن بنجاح...")
    tasks = [start_protection_for_user(user, tg_id) for user, tg_id in PROTECTED_USERS.items()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
