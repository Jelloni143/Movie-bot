#!/usr/bin/env python3
"""
Render-deployable FREE VIDEO BOT  (requests only)
"""
import os, logging, re, requests, html, time, random
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)

BOT_TOKEN = os.environ["BOT_TOKEN"]      # Render dashboard me daalna hai

HEADERS = {"User-Agent": "Mozilla/5.0 (Linux; Android 11)"}
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# ================= SAME SEARCH FUNCTIONS =================
def youtube_stream(page_url: str):
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=12)
        match = re.search(r'"formats":\s*(\[.*?\]),', r.text)
        if not match: return None, None
        formats = eval(match.group(1))
        for f in formats:
            if f.get("height", 0) <= 720 and f.get("url"):
                return f.get("title", "YouTube video"), f["url"]
    except Exception as e:
        logger.debug("YT stream fail: %s", e)
    return None, None

def yt_search(query: str):
    term = re.sub(r"\s+", " ", query).strip().replace(" ", "+")
    channels = [
        ("@GoldminesTelefilms", "https://www.youtube.com/@GoldminesTelefilms/search?query={}"),
        ("@ShemarooMovies",     "https://www.youtube.com/@ShemarooMovies/search?query={}"),
        ("@rajshri",            "https://www.youtube.com/@rajshri/search?query={}")
    ]
    for ch, temp in channels:
        try:
            r = requests.get(temp.format(term), headers=HEADERS, timeout=10)
            soup = BeautifulSoup(r.text, "html.parser")
            a = soup.select_one('a[href*="/watch?v="]')
            if a:
                page_url = "https://www.youtube.com" + a["href"]
                title, stream_url = youtube_stream(page_url)
                if stream_url: return f"{title}  ({ch})", stream_url
        except: pass
        time.sleep(0.4)
    return None, None

def mx_search(query: str):
    try:
        term = re.sub(r"\s+", " ", query).strip().replace(" ", "-")
        r = requests.get(f"https://www.mxplayer.in/search/{term}", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for a in soup.select('a[href*="/show/"]')[:4]:
            return html.unescape(a.get_text(strip=True)), "https://www.mxplayer.in" + a["href"]
    except: pass
    return None, None

def zee5_search(query: str):
    try:
        term = re.sub(r"\s+", " ", query).strip().replace(" ", "%20")
        r = requests.get(f"https://www.zee5.com/global/search/{term}", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        for div in soup.select('div[data-card-type="FREE"]')[:3]:
            a = div.select_one("a[href]")
            if a: return html.unescape(a.get("title", "")), "https://www.zee5.com" + a["href"]
    except: pass
    return None, None

def find_movie(query: str):
    name, url = yt_search(query)
    if url: return name, url, "video"
    name, url = mx_search(query)
    if url: return name, url, "page"
    name, url = zee5_search(query)
    if url: return name, url, "page"
    return None, None, None

def get_random_movie():
    channels = [
        "https://www.youtube.com/@GoldminesTelefilms/videos",
        "https://www.youtube.com/@ShemarooMovies/videos",
        "https://www.youtube.com/@rajshri/videos"
    ]
    try:
        pick = random.choice(channels)
        r  = requests.get(pick, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="/watch?v="]')[:10]
        if links:
            a = random.choice(links)
            page_url = "https://www.youtube.com" + a["href"]
            title, stream_url = youtube_stream(page_url)
            if stream_url: return title, stream_url, "video"
    except: pass
    try:
        r = requests.get("https://www.mxplayer.in/movies", headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.select('a[href*="/show/"]')
        if items:
            pick = random.choice(items)
            title = html.unescape(pick.get_text(strip=True))
            link  = "https://www.mxplayer.in" + pick["href"]
            return title, link, "page"
    except: pass
    return None, None, None

# ================= HANDLERS =================
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("🎲 Random Movie", callback_data="random")]]
    await update.message.reply_text(
        "🎬 *Direct VIDEO Bot (Render)*\n"
        "1. Movie naam bhejo – **YouTube direct .mp4** milega!\n"
        "2. Nahi mili to MX / Zee5 player page khulega.\n"
        "3. `🎲 Random Movie` → instant playable video / page!",
        parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb)
    )

async def random_movie(update: Update, _: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("⏳ Picking random video …")
    wait = await query.message.reply_text("🎲 Finding random playable video …")
    title, url, typ = get_random_movie()
    if not url:
        await wait.edit_text("❌ Random fail ho gaya! /start se dubara try kar.")
        return
    btn_text = "▶️ Watch Now (Direct)" if typ == "video" else "📽️ Open Player"
    kb = [[InlineKeyboardButton(btn_text, url=url)]]
    await wait.edit_text(f"🎬 *Random {typ}:* `{html.escape(title)}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def movie_handler(update: Update, _: ContextTypes.DEFAULT_TYPE):
    q = update.message.text
    wait = await update.message.reply_text("🔍 Searching YouTube → MX → Zee5 …")
    title, url, typ = find_movie(q)
    if not url:
        await wait.edit_text("❌ Kahi bhi nahi mili! Exact / English name ya /random try kar.")
        return
    btn_text = "▶️ Watch Now (Direct)" if typ == "video" else "📽️ Open Player"
    kb = [[InlineKeyboardButton(btn_text, url=url)]]
    await wait.edit_text(f"✅ Found *{typ}:* `{html.escape(title)}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, movie_handler))
    app.add_handler(CallbackQueryHandler(random_movie, pattern="^random$"))
    logger.info("Render bot started")
    # Render health-check ke liye dummy web hook
    from flask import Flask, request
    flask_app = Flask(__name__)

    @flask_app.route("/")
    def home():
        return "Bot is alive!", 200

    # Run bot in thread so Flask stays alive
    import threading
    threading.Thread(target=app.run_polling, daemon=True).start()
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__": main()
