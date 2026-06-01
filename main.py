import os
import json
import yt_dlp
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

BOT_TOKEN = "8930290832:AAHCi2UEb7YF2CmaIray64vEU-g61fqQmL8"
ADMIN_ID = 5831689535
CHANNEL = "@ffedya_571"
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(list(users), f)

users = load_users()

async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

def sub_keyboard():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL[1:]}"),
        InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")
    ]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.add(user.id)
    save_users(users)
    if not await is_subscribed(user.id, context):
        await update.message.reply_text(f"👋 Salom, *{user.first_name}*!\n\n⚠️ Botdan foydalanish uchun\n📢 Kanalga obuna bo'ling!", parse_mode="Markdown", reply_markup=sub_keyboard())
        return
    await update.message.reply_text(f"👋 Salom, *{user.first_name}*! 🎵\n\n🎧 *SONGSET BOT*\n━━━━━━━━━━━━━━\n\n📎 Havola yuboring:\n• 🎬 YouTube\n• 📸 Instagram\n• 🎵 TikTok\n• 🎶 SoundCloud\n\n⚡ Bot tez va sifatli ishlaydi!", parse_mode="Markdown")

async def check_sub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_subscribed(query.from_user.id, context):
        await query.message.edit_text("✅ *Obuna tasdiqlandi!*\n\n🎵 Endi video havolasini yuboring!", parse_mode="Markdown")
    else:
        await query.answer("❌ Hali obuna bo'lmadingiz!", show_alert=True)

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.add(user.id)
    save_users(users)
    if not await is_subscribed(user.id, context):
        await update.message.reply_text("⚠️ Avval kanalga obuna bo'ling!", reply_markup=sub_keyboard())
        return
    url = update.message.text.strip()
    if not url.startswith("http"):
        await update.message.reply_text("❌ Havola yuboring!")
        return
    msg = await update.message.reply_text("⏳ *Yuklanmoqda...*", parse_mode="Markdown")
    output_path = f"audio_{update.message.message_id}"
    ydl_opts = {'format': 'bestaudio/best', 'outtmpl': output_path + '.%(ext)s', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'quiet': True}
    try:
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Musiqa')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', '') or ''
        if duration and duration > 1800:
            await msg.edit_text("❌ Video 30 daqiqadan uzun!")
            return
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        audio_file = output_path + '.mp3'
        if not os.path.exists(audio_file):
            await msg.edit_text("❌ Yuklashda xatolik!")
            return
        await msg.edit_text("🚀 *Yuborilmoqda...*", parse_mode="Markdown")
        with open(audio_file, 'rb') as f:
            await update.message.reply_audio(audio=f, title=title[:64], performer=uploader[:64] if uploader else "SONGSET", caption=f"🎵 *{title[:80]}*\n━━━━━━━━━━━━━━\n⚡ @{CHANNEL[1:]}", parse_mode="Markdown")
        os.remove(audio_file)
        await msg.delete()
    except Exception:
        await msg.edit_text("❌ Xatolik! Boshqa havola yuboring.")
        for ext in ['.mp3', '.webm', '.m4a']:
            if os.path.exists(output_path + ext):
                os.remove(output_path + ext)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    await update.message.reply_text(f"📊 *Statistika*\n👥 Foydalanuvchilar: *{len(users)}* ta\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("❌ /broadcast Xabar matni")
        return
    text = " ".join(context.args)
    success = 0
    for user_id in list(users):
        try:
            await context.bot.send_message(user_id, f"📢 {text}")
            success += 1
        except:
            pass
    await update.message.reply_text(f"✅ {success} ta foydalanuvchiga yuborildi!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CallbackQueryHandler(check_sub, pattern="check_sub"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("✅ SONGSET Bot ishlamoqda...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
