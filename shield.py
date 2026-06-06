import asyncio
import json
import os
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 1. إعدادات تليجرام الأساسية
TELEGRAM_TOKEN = "8287206695:AAG-ddOXd8zPhIHG_ivTx5Iq45zeWoChwD4"
ADMIN_CHAT_ID = 7896705259  # تم تنظيف السطر من المسافات المخفية

# إنشاء كائن البوت للإرسال المباشر
tg_bot = Bot(token=TELEGRAM_TOKEN)
DATA_FILE = "protected_list.json"
active_tasks = {}

def load_users():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"ahmedtop373": ADMIN_CHAT_ID, "roch.roch765": ADMIN_CHAT_ID}

def save_users(users):
    with open(DATA_FILE, "w") as f:
        json.dump(users, f)

PROTECTED_USERS = load_users()

MALICIOUS_INDICATORS = [
    "http", "www", "://", ".com", ".net", ".xyz", ".ru", ".cc",
    "<script", "javascript", "html", "href", "bot", "crack", 
    "\\", "&&", "$", "{"
]

async def start_protection_for_user(tiktok_username, telegram_id):
    client = TikTokLiveClient(unique_id=tiktok_username)
    print(f"🛡️ جدار الحماية بدأ بمراقبة لايف الحساب: @{tiktok_username}")

    @client.on(CommentEvent)
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
            # محاولة كتم المستخدم في التيك توك (تحتاج صلاحيات موديريتور في الحساب الصاحب اللايف)
            try: 
                await event.user.mute(duration=99999)
            except Exception as e: 
                print(f"⚠️ تعذر كتم المستخدم على تيك توك: {e}")
            
            # إرسال إشعار للأدمن الخاص بالـ بوت
            try: 
                await tg_bot.send_message(chat_id=ADMIN_CHAT_ID, text=alert_message, parse_mode="Markdown")
            except Exception as e: 
                print(f"❌ خطأ في إرسال التنبيه للأدمن: {e}")
            
            # إرسال إشعار لصاحب الحساب إذا لم يكن هو الأدمن نفسه
            if str(telegram_id) != str(ADMIN_CHAT_ID):
                try: 
                    await tg_bot.send_message(chat_id=int(telegram_id), text=alert_message, parse_mode="Markdown")
                except Exception as e: 
                    print(f"❌ خطأ في إرسال التنبيه للمستخدم: {e}")

    try:
        await client.start()
    except Exception as err:
        print(f"❌ تعذر الاتصال بـ لايف @{tiktok_username} حالياً أو اللايف مغلق: {err}")

# تحديث الدالة لتتوافق مع الإصدار الجديد v20+
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id != ADMIN_CHAT_ID:
        await update.message.reply_text("❌ عذراً، هذا الأمر متاح للمسؤول فقط!")
        return

    try:
        tiktok_user = context.args[0]
        friend_tg_id = context.args[1]
        
        users = load_users()
        users[tiktok_user] = int(friend_tg_id)
        save_users(users)
        
        await update.message.reply_text(f"✅ تم إضافة الحساب لدرع الحماية بنجاح:\n👤 تيك توك: @{tiktok_user}\n🆔 تليجرام: {friend_tg_id}")
        
        # تشغيل حماية الحساب الجديد في الخلفية مباشرة دون التأثير على البوت
        task = asyncio.create_task(start_protection_for_user(tiktok_user, int(friend_tg_id)))
        active_tasks[tiktok_user] = task
        
    except (IndexError, ValueError):
        await update.message.reply_text("⚠️ اكتب الأمر بهذا الشكل:\n`/add اسم_الحساب id_التليجرام`")

async def main():
    # 1. بناء وتجهيز بوت التليجرام بالإصدار الجديد
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("add", add_user))
    
    # 2. تشغيل حماية الحسابات المحفوظة مسبقاً في الخلفية
    for user, tg_id in PROTECTED_USERS.items():
        task = asyncio.create_task(start_protection_for_user(user, tg_id))
        active_tasks[user] = task

    # 3. تشغيل البوت والانتظار لاستقبال الأوامر (تجمع بين الـ Loop للبوت والتيك توك معاً)
    async with application:
        await application.initialize()
        await application.start()
        print("🤖 بوت التحكم عبر تليجرام يعمل الآن...")
        await application.updater.start_polling()
        
        # الحفاظ على تشغيل البرنامج بشكل دائم ومستمر
        while True:
            await asyncio.sleep(3600)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\n🛑 تم إيقاف درع الحماية والبوت.")