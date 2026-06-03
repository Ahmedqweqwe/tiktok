import os
import asyncio
import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ضع توكن البوت الخاص بك هنا
TOKEN = "8959485190:AAE3Wegyu2E1I80iknKfJKH8QNumM7x7tMuk"

# أمر ترحيب البوت عند الضغط على /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت معلومات تيك توك!\n"
        "🔍 أرسل لي اسم مستخدم (Username) لأجلب لك بياناته الحالية فوراً."
    )

# دالة جلب البيانات من واجهة برمجة تيك توك المفتوحة
async def fetch_tiktok_data(username: str):
    # نستخدم واجهة API عامة ومستقرة، يمكنك استبدالها برابط الـ API الخاص بك إذا أردت
    url = f"https://tiktokv.com{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            return None
    return None

# معالجة الرسائل القادمة من المستخدمين
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    await update.message.reply_text("🔄 جاري البحث وسحب بيانات الحساب من تيك توك...")
    
    data = await fetch_tiktok_data(username)
    
    if data and "user_list" in data and len(data["user_list"]) > 0:
        user_info = data["user_list"][0]["user_info"]
        
        # استخراج البيانات بصيغة مرتبة
        nickname = user_info.get("nickname", "غير معروف")
        custom_verify = "نعم ✅" if user_info.get("custom_verify") else "لا ❌"
        follower_count = user_info.get("follower_count", 0)
        following_count = user_info.get("following_count", 0)
        total_favorited = user_info.get("total_favorited", 0)
        aweme_count = user_info.get("aweme_count", 0) # عدد الفيديوهات
        
        msg = (
            f"👤 **اسم المستخدم:** `{username}`\n"
            f"🆔 **الاسم:** {nickname}\n"
            f"👥 **المتابعين:** {follower_count:,}\n"
            f"📉 **يتابع:** {following_count:,}\n"
            f"❤️ **الإعجابات:** {total_favorited:,}\n"
            f"🎥 **الفيديوهات:** {aweme_count}\n"
            f"🌟 **حساب موثق:** {custom_verify}"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ عذراً، لم نتمكن من العثور على الحساب. تأكد من كتابة اسم المستخدم بشكل صحيح.")

def main():
    # بناء البوت وبدء تشغيله
    application = Application.builder().token(TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 البوت يعمل الآن بنجاح...")
    application.run_polling()

if __name__ == "__main__":
    main()
