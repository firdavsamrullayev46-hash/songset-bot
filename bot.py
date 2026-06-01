import asyncio
import logging
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import FSInputFile
from dotenv import load_dotenv
import yt_dlp

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")

DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
cache = {}

YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': str(DOWNLOADS_DIR / '%(id)s.%(ext)s'),
    'quiet': True,
    'no_warnings': True,
    'ignoreerrors': True,
}

def extract_shortcode(url: str) -> str | None:
    match = re.search(r'instagram\.com/(?:p|reel|tv)/([a-zA-Z0-9_\-]+)', url)
    return match.group(1) if match else None

async def download_media(url: str) -> str | None:
    shortcode = extract_shortcode(url)
    if not shortcode:
        return None
    if shortcode in cache and Path(cache[shortcode]).exists():
        return cache[shortcode]
    loop = asyncio.get_running_loop()
    try:
        def dl():
            with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
                info = ydl.extract_info(url, download=True)
                if info and 'requested_downloads' in info:
                    return info['requested_downloads'][0]['filepath']
                return None
        filepath = await loop.run_in_executor(None, dl)
        if filepath and Path(filepath).exists():
            cache[shortcode] = str(filepath)
            return str(filepath)
        return None
    except Exception as e:
        logger.exception(f"Yuklash xatosi: {e}")
        return None

async def cleanup(filepath: str, delay: int = 20):
    await asyncio.sleep(delay)
    try:
        if Path(filepath).exists():
            Path(filepath).unlink()
    except Exception as e:
        logger.error(f"Tozalash xatosi: {e}")

@dp.message(Command("start"))
async def start_cmd(msg: types.Message):
    await msg.answer("🎬 Instagram yuklab oluvchi bot. Instagram havolasini yuboring.")

@dp.message()
async def handle(msg: types.Message):
    url = msg.text.strip()
    if not re.search(r'instagram\.com/(p|reel|tv)/', url):
        await msg.answer("❌ Faqat Instagram havolasini yuboring.")
        return
    status = await msg.answer("⏳ Yuklanmoqda...")
    filepath = await download_media(url)
    if not filepath:
        await status.edit_text("❌ Yuklab bo‘lmadi.")
        return
    try:
        video = FSInputFile(filepath)
        await msg.answer_video(video, caption="✅ Yuklab olindi", supports_streaming=True)
        await status.delete()
        asyncio.create_task(cleanup(filepath))
    except Exception:
        await status.edit_text("❌ Yuborishda xatolik (fayl hajmi 50MB dan oshgan bo‘lishi mumkin).")

async def main():
    logger.info("Bot ishga tushdi")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())