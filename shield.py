import sys
import os
import json
import asyncio
import types

# حل مشكلة توافق المكتبات في الإصدارات الحديثة لمنصات الاستضافة
try:
    import imghdr
except ImportError:
    imghdr_mock = types.ModuleType("imghdr")
    imghdr_mock.what = lambda file, h=None: None
    sys.modules["imghdr"] = imghdr_mock

import aiohttp
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, ConnectEvent

# --- ⚙️ الإعدادات المحدثة والصحيحة بنسبة 100% ---
TELEGRAM_TOKEN = "8287206695:AAG-ddOXd8zPhIHG_ivTx5Iq45zeWoChwD4"  # التوكن الصحيح الخاص بك
ADMIN_CHAT_ID = 7896705259                                         # الآيدي الخاص بك

DATA_FILE = "protected_list.json"
protected_users = set()
active_tasks = {}

# --- 📁 إدارة ملف الحسابات المحمية ---
def load_users():
    global protected_users
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    protected_users = {name.strip().lower() for name in data if name}
        except Exception as e:
            print(f"Error loading file: {e}")

def save_users():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(list(protected_users), f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Error saving file: {e}")

# --- 🛡️ مراقبة بث تيك توك لايف ---
async def start_tiktok_listener(username, bot_instance):
    async def run_client():
        try:
            client = TikTokLiveClient(unique_id=username)
            
            @client.on("connect")
            async def on_connect(event: ConnectEvent):
                try:
                    await bot_instance.send_message(chat_id=ADMIN_CHAT_ID, text=f"🟢 تم بدء حماية ومراقبة بث الحساب: {username}")
                except Exception as ex:
                    print(f"Telegram error: {ex}")

            @client.on("comment")
            async def on_comment(event: CommentEvent):
                log_text = f"💬 [{username}] {event.user.unique_id}: {event.comment}"
                print(log_text)
                try:
                    await bot_instance.send_message(chat_id=ADMIN_CHAT_ID, text=log_text)
                except Exception as ex:
                    print(f"Telegram report error: {ex}")

            await client.start()
        except Exception as e:
            print(f"Error in live listener for {username}: {e}")
            if username in active_tasks:
                del active_tasks[username]

    task = asyncio.create_task(run_client())
    active_tasks[username] = task

# --- 🤖 أوامر تليجرام للتحكم الكامل لحسابك فقط ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    await update.message.reply_text("👋 أهلاً بك يا رئيس! أنا بوت حماية بث تيك توك.\n\n"
                                    "➕ لإضافة حساب للحماية: `/add username`\n"
                                    "❌ لإزالة حساب: `/remove username`\n"
                                    "📋 لعرض المحميين: `/list`", parse_mode="Markdown")

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text("⚠️ يرجى كتابة يوزر الحساب، مثال:\n`/add roch.roch765`", parse_mode="Markdown")
        return
    username = context.args[0].strip().lower().replace("@", "")
    if username in protected_users:
        await update.message.reply_text(f"ℹ️ الحساب {username} مضاف بالفعل.")
        return
    protected_users.add(username)
    save_users()
    await start_tiktok_listener(username, context.application.bot)
    await update.message.reply_text(f"✅ تم إضافة `{username}` لقائمة الحماية وبدء مراقبته الحية.", parse_mode="Markdown")

async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    if not context.args:
        await update.message.reply_text("⚠️ يرجى كتابة يوزر الحساب لإزالته، مثال:\n`/remove username`", parse_mode="Markdown")
        return
    username = context.args[0].strip().lower().replace("@", "")
    if username in protected_users:
        protected_users.remove(username)
        save_users()
        if username in active_tasks:
            active_tasks[username].cancel()
            del active_tasks[username]
        await update.message.reply_text(f"❌ تم إزالة الحساب `{username}` من قائمة الحماية.", parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ هذا الحساب غير موجود بالقائمة.")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_CHAT_ID:
        return
    if not protected_users:
        await update.message.reply_text("📋 قائمة الحماية فارغة حالياً.")
        return
    msg = "📋 **قائمة الحسابات المحمية حالياً:**\n\n"
    for user in protected_users:
        status = "🟢 نشط" if user in active_tasks else "💤 في الانتظار"
        msg += f"- `{user}` ({status})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- 🚀 تشغيل البوت الموحد بدون مشاكل Loops ---
def run_bot():
    load_users()
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("remove", remove_user))
    application.add_handler(CommandHandler("list", list_users))

    print("🚀 البوت مستعد ويعمل الآن بنجاح...")
    application.run_polling(close_loop=False, allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    run_bot()
