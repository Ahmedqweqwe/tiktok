import sys
import os
import json
import asyncio
import aiohttp
import types

# تلافي مشكلة مكتبة imghdr في الإصدارات الحديثة
try:
    import imghdr
except ImportError:
    imghdr_mock = types.ModuleType("imghdr")
    imghdr_mock.what = lambda file, h=None: None
    sys.modules["imghdr"] = imghdr_mock

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent

# --- ⚙️ الإعدادات الأساسية (تأكد من تعديلها) ---
TOKEN = "8607011325:AAHbC_Xz7kbylCoYvneUuktU7ngmzt_6KW0"    
CHAT_ID = 7896705259                  
PROXY_URL = "http://proxy.server:3128" # البروكسي الخاص بـ PythonAnywhere

PROTECTED_FILE = "protected_list.json"
protected_users = set()

# تشغيل وإدارة مهام البث النشطة
active_tasks = {}

# --- 📁 إدارة ملف المستخدمين المحميين ---
def load_protected_list():
    global protected_users
    if os.path.exists(PROTECTED_FILE):
        try:
            with open(PROTECTED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    protected_users = {name.strip().lower() for name in data if name}
                    print(f"📦 تم تحميل {len(protected_users)} مستخدم محمي.")
        except Exception as e:
            print(f"خطأ في تحميل الملف: {e}")

def save_protected_list():
    try:
        with open(PROTECTED_FILE, "w", encoding="utf-8") as f:
            json.dump(list(protected_users), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ في حفظ الملف: {e}")

# --- 🛡️ دالة مراقبة بث التيك توك ---
async def start_tiktok_monitor(username, app_bot):
    async def run_client():
        try:
            client = TikTokLiveClient(unique_id=username)
            
            @client.on("connect")
            async def on_connect(event: ConnectEvent):
                await app_bot.send_message(chat_id=CHAT_ID, text=f"🟢 تم بدء حماية ومراقبة بث الحساب: {username}")

            @client.on("comment")
            async def on_comment(event: CommentEvent):
                # هنا يمكنك إضافة شروط الفلترة أو الحظر للحماية
                log_text = f"💬 [{username}] {event.user.unique_id}: {event.comment}"
                print(log_text)
                await app_bot.send_message(chat_id=CHAT_ID, text=log_text)

            await client.start()
        except Exception as e:
            print(f"خطأ في مراقبة {username}: {e}")
            if username in active_tasks:
                del active_tasks[username]

    task = asyncio.create_task(run_client())
    active_tasks[username] = task

# --- 🤖 أوامر التحكم الخاصة بك (تليجرام) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return  # تجاهل أي شخص آخر يحاول التحكم بالبوت
    await update.message.reply_text("👋 أهلاً بك يا رئيس! أنا بوت حماية بث تيك توك.\n\n"
                                    "➕ لإضافة حساب للحماية: `/add username`\n"
                                    "❌ لإزالة حساب: `/remove username`\n"
                                    "📋 لعرض المحميين: `/list`")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ يرجى كتابة يوزر الحساب، مثال:\n`/add roch.roch765`")
        return
        
    username = context.args[0].strip().lower().replace("@", "")
    if username in protected_users:
        await update.message.reply_text(f"ℹ️ الحساب {username} مضاف بالفعل في قائمة الحماية.")
        return
        
    protected_users.add(username)
    save_protected_list()
    
    # تشغيل الحماية فورا للحساب المضاف
    await start_tiktok_monitor(username, context.application.bot)
    await update.message.reply_text(f"✅ تم إضافة الحساب `{username}` لقائمة الحماية وبدء مراقبته.")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
        
    if not context.args:
        await update.message.reply_text("⚠️ يرجى كتابة يوزر الحساب لإزالته، مثال:\n`/remove username`")
        return
        
    username = context.args[0].strip().lower().replace("@", "")
    if username in protected_users:
        protected_users.remove(username)
        save_protected_list()
        
        # إيقاف مهمة المراقبة إذا كانت تعمل
        if username in active_tasks:
            active_tasks[username].cancel()
            del active_tasks[username]
            
        await update.message.reply_text(f"❌ تم إزالة الحساب `{username}` من قائمة الحماية وإيقاف المراقبة.")
    else:
        await update.message.reply_text("⚠️ هذا الحساب غير موجود بالقائمة.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != CHAT_ID:
        return
    if not protected_users:
        await update.message.reply_text("📋 قائمة الحماية فارغة حالياً.")
        return
    
    msg = "📋 **قائمة الحسابات المحمية حالياً:**\n\n"
    for user in protected_users:
        status = "🟢 نشط" if user in active_tasks else "💤 في الانتظار"
        msg += f"- `{user}` ({status})\n"
    await update.message.reply_text(msg)

# --- 🚀 تشغيل البوت الموحد ---
async def main():
    load_protected_list()
    
    # بناء تطبيق تليجرام مع البروكسي المتوافق مع سرفرات PythonAnywhere المجانية
    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        builder.proxy(PROXY_URL)
        builder.get_updates_proxy(PROXY_URL)
    
    application = builder.build()
    
    # تسجيل الأوامر والتحكم
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("list", list_users))
    
    await application.initialize()
    await application.start()
    
    # بدء تشغيل المراقبة تلقائياً لجميع الحسابات المخزنة مسبقاً عند إقلاع البوت
    for user in protected_users:
        await start_tiktok_monitor(user, application.bot)
        
    print("🚀 البوت يعمل الآن بنجاح وينتظر أوامرك على تليجرام...")
    
    # إبقاء البوت مستمراً في العمل (Polling)
    await application.updater.start_polling()
    
    # حلقة حماية لمنع إغلاق الدالة الأساسية
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت.")
