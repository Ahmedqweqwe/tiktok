import asyncio
import json
import os
from TikTokLive import TikTokLiveClient
from TikTokLive.types.events import CommentEvent
from telegram import Bot
from telegram.ext import Updater, CommandHandler, CallbackContext
from telegram import Update

# 1. إعدادات تليجرام الأساسية (بياناتك مدمجة وجاهزة)
TELEGRAM_TOKEN = "8287206695:AAG-ddOXd8zPhIHG_ivTx5Iq45zeWoChwD4"
ADMIN_CHAT_ID = 7896705259  # رقم الـ ID الخاص بك (المسؤول)

tg_bot = Bot(token=TELEGRAM_TOKEN)
DATA_FILE = "protected_list.json"

# دالة لتحميل قائمة الحماية من ملف الذاكرة تلقائياً
def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"ahmedtop373": ADMIN_CHAT_ID, "roch.roch765": ADMIN_CHAT_ID}

# دالة لحفظ القائمة المحدثة
def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

PROTECTED_USERS = load_users()
active_tasks = {}

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
        if any(indicator in comment_text for indicator in MALICIOUS_INDICATORS):
            alert_message = (
                f"🚨 ⚠️ **محاولة هجوم مكتشفة!** ⚠️\n\n"
                f"📺 **اللايف المستهدف:** `@{tiktok_username}`\n"
                f"👤 **المهاجم:** `@{event.user.unique_id}`\n"
                f"💬 **السكريبت/الرابط المرسل:**\n`{event.comment}`\n\n"
                f"🛠️ يرجى حظره فوراً من الهاتف!"
            )
            try: await event.user.mute(duration=99999)
            except: pass
            
            try: await tg_bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_message, parse_mode="Markdown")
            except: pass
            
            if str(telegram_id) != str(ADMIN_CHAT_ID):
                try: await tg_bot.send_message(chat_id=int(telegram_id), text=alert_message, parse_mode="Markdown")
                except: pass

    try:
        await client.start()
    except Exception as err:
        print(f"❌ تعذر الاتصال بـ لايف @{tiktok_username} حالياً: {err}")

# أمر تليجرام لإضافة صديق جديد من الهاتف فوراً
def add_user(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if chat_id != ADMIN_CHAT_ID:
        update.message.reply_text("❌ عذراً، هذا الأمر متاح للمسؤول فقط!")
        return

    try:
        # الكود يتوقع منك إرسال: /add يوزر_تيكتوك id_تليجرام
        tiktok_user = context.args[0]
        friend_tg_id = context.args[1]
        
        users = load_users()
        users[tiktok_user] = int(friend_tg_id)
        save_users(users)
        
        update.message.reply_text(f"✅ تم إضافة الحساب لدرع الحماية السحابي بنجاح:\n👤 تيك توك: @{tiktok_user}\n🆔 تليجرام: {friend_tg_id}\n\n⚙️ جاري تشغيل الحماية تلقائياً...")
        
        # تشغيل حماية الحساب الجديد في الخلفية فوراً دون إعادة تشغيل السيرفر
        loop = asyncio.get_event_loop()
        task = loop.create_task(start_protection_for_user(tiktok_user, int(friend_tg_id)))
        active_tasks[tiktok_user] = task
        
    except (IndexError, ValueError):
        update.message.reply_text("⚠️ طريقة كتابة الأمر خاطئة!\nاكتب الأمر بهذا الشكل تماماً:\n`/add اسم_حساب_التيكتوك id_التليجرام`")

async def run_tiktok_shield():
    loop = asyncio.get_event_loop()
    for user, tg_id in PROTECTED_USERS.items():
        task = loop.create_task(start_protection_for_user(user, tg_id))
        active_tasks[user] = task

def start_telegram_bot():
    updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("add", add_user))
    
    updater.start_polling()
    print("🤖 بوت التحكم عبر تليجرام يعمل الآن...")

if __name__ == "__main__":
