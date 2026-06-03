import asyncio
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = "8959485190:AAE3Wegyu2E1I80iknKfJKH8QNumM7x7tMuk"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت معلومات تيك توك!\n"
        "🔍 أرسل لي اسم مستخدم (Username) لأجلب لك بياناته الحالية فوراً."
    )

def fetch_tiktok_data(username: str):
    url = f"https://tiktokv.com{username}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json()
    except:
        return None
    return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.message.text.strip().replace("@", "")
    await update.message.reply_text("🔄 جاري البحث وسحب بيانات الحساب من تيك توك...")
    
    # تشغيل طلب الشبكة في الخلفية لتفادي التعليق
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, fetch_tiktok_data, username)
    
    if data and "user_list" in data and len(data["user_list"]) > 0:
        user_info = data["user_list"][0]["user_info"]
        
        msg = f"👤 **اسم المستخدم:** `{username}`\n" \
              f"🆔 **الاسم:** {user_info.get('nickname', 'غير معروف')}\n" \
              f"👥 **المتابعين:** {user_info.get('follower_count', 0):,}\n" \
              f"📉 **يتابع:** {user_info.get('following_count', 0):,}\n" \
              f"❤️ **الإعجابات:** {user_info.get('total_favorited', 0):,}\n" \
              f"🎥 **الفيديوهات:** {user_info.get('aweme_count', 0)}\n" \
              f"🌟 **حساب موثق:** {'نعم ✅' if user_info.get('custom_verify') else 'لا ❌'}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ عذراً، لم نتمكن من العثور على الحساب. تأكد من الاسم.")

def main():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(filters.TEXT & ~filters.COMMAND, handle_message)
    print("🤖 البوت يعمل الآن...")
    application.run_polling()

if __name__ == "__main__":
    main()
