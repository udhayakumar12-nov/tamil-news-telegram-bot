print("🚀 Bot is starting...")

import os
import asyncio
import csv
import sqlite3
import requests
import feedparser
from datetime import datetime
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# ---------- CONFIGURATION ----------
import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = 8623813419

# ---------- DATABASE SETUP ----------
def init_db():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (chat_id INTEGER PRIMARY KEY, 
                  username TEXT,
                  first_name TEXT,
                  subscribed_date TIMESTAMP)''')
    conn.commit()
    conn.close()

def add_user(chat_id, username, first_name):
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (chat_id, username, first_name, subscribed_date)
                 VALUES (?, ?, ?, ?)''', 
              (chat_id, username, first_name, datetime.now()))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT chat_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

def get_user_count():
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

# ---------- BBC NEWS ----------
def get_bbc_news():
    news_list = []
    try:
        url = "https://www.bbc.com/tamil"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        headlines = soup.find_all(['h3', 'h2'])
        
        for headline in headlines[:10]:
            link_tag = headline.find('a')
            if link_tag:
                title = link_tag.get_text(strip=True)
                href = link_tag.get('href', '')
                if title and len(title) > 15:
                    if href.startswith('/'):
                        full_url = "https://www.bbc.com" + href
                    else:
                        full_url = href
                    news_list.append(f"📌 *{title}*\n🔗 [Read more]({full_url})\n🏷️ *Source:* பிபிசி தமிழ்")
        print(f"✅ BBC - {len(news_list)} செய்திகள்")
    except Exception as e:
        print(f"❌ BBC பிழை: {e}")
    return news_list

# ---------- ENGLISH NEWS ----------
def get_english_news():
    news_list = []
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/news/world/rss.xml')
        for entry in feed.entries[:8]:
            title = entry.title
            link = entry.link
            news_list.append(f"📌 *{title}*\n🔗 [Read more]({link})\n🏷️ *Source:* BBC World (English)")
        print(f"✅ English News - {len(news_list)} செய்திகள்")
    except Exception as e:
        print(f"❌ English RSS error: {e}")
    return news_list

# ---------- DAILY THANTHI NEWS ----------
def get_dailythanthi_news():
    news_list = []
    driver = None
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get("https://www.dailythanthi.com/")
        driver.implicitly_wait(5)
        
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/news/')]")
        
        for element in elements[:10]:
            title = element.text.strip()
            link = element.get_attribute('href')
            if title and len(title) > 20:
                news_list.append(f"📌 *{title}*\n🔗 [Read more]({link})\n🏷️ *Source:* தினத்தந்தி")
        print(f"✅ தினத்தந்தி - {len(news_list)} செய்திகள்")
    except Exception as e:
        print(f"❌ தினத்தந்தி பிழை: {e}")
    finally:
        if driver:
            driver.quit()
    return news_list

# ---------- SEARCH FUNCTION ----------
def search_news(keyword):
    all_news = get_bbc_news() + get_dailythanthi_news()
    filtered = [news for news in all_news if keyword.lower() in news.lower()]
    return filtered

# ---------- TELEGRAM HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        f"வணக்கம் {user.first_name}! 👋\n\n"
        "நீங்கள் எங்கள் செய்திச் சேவையில் பதிவு செய்யப்பட்டுள்ளீர்கள்!\n\n"
        "📰 /menu - செய்தி வகைகளைப் பார்க்க\n"
        "🔍 /search <keyword> - செய்திகளைத் தேட\n"
        "👥 /stats - மொத்த subscribers (Admin only)\n"
        "📢 /broadcast - அனைவருக்கும் செய்தி (Admin only)\n"
        "/help - உதவி"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔧 கட்டளைகள்:\n\n"
        "/start - Bot-ஐ தொடங்க\n"
        "/menu - செய்தி வகைகளைப் பார்க்க\n"
        "/news - உடனடிச் செய்திகள்\n"
        "/search <keyword> - செய்திகளைத் தேட\n"
        "/stats - மொத்த subscribers (Admin only)\n"
        "/broadcast - அனைவருக்கும் செய்தி (Admin only)\n"
        "/help - உதவி"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ இந்தக் கட்டளையைப் பயன்படுத்த உங்களுக்கு அனுமதி இல்லை.")
        return
    count = get_user_count()
    await update.message.reply_text(f"👥 மொத்த subscribers: {count}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ இந்தக் கட்டளையைப் பயன்படுத்த உங்களுக்கு அனுமதி இல்லை.")
        return
    message_text = " ".join(context.args)
    if not message_text:
        await update.message.reply_text("⚠️ /broadcast [உங்கள் செய்தி] - செய்தியை உள்ளிடவும்")
        return
    users = get_all_users()
    success_count = 0
    fail_count = 0
    status_msg = await update.message.reply_text(f"📢 செய்தி அனுப்பப்படுகிறது... {len(users)} பேருக்கு")
    for chat_id in users:
        try:
            await context.bot.send_message(chat_id=chat_id, text=message_text)
            success_count += 1
            await asyncio.sleep(0.05)
        except Exception as e:
            fail_count += 1
    await status_msg.edit_text(
        f"✅ Broadcast முடிந்தது!\n\n"
        f"📨 வெற்றி: {success_count}\n"
        f"❌ தோல்வி: {fail_count}\n"
        f"👥 மொத்தம்: {len(users)}"
    )

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 செய்திகள் சேகரிக்கப்படுகிறது. சிறிது பொறுக்கவும்...")
    
    all_news = []
    bbc_news = get_bbc_news()
    dt_news = get_dailythanthi_news()
    all_news.extend(bbc_news)
    all_news.extend(dt_news)
    
    if all_news:
        message = "📰 *பல தள செய்திகள்:*\n\n" + "\n\n".join(all_news[:15])
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ எந்த தளத்திலிருந்தும் செய்திகள் கிடைக்கவில்லை.")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyword = " ".join(context.args)
    if not keyword:
        await update.message.reply_text("🔍 *Usage:* /search <keyword>\n\nExample: /search தேர்தல்", parse_mode='Markdown')
        return
    
    await update.message.reply_text(f"🔍 *Searching for '{keyword}'...*", parse_mode='Markdown')
    filtered = search_news(keyword)
    
    if filtered:
        message = "🔎 *Search Results:*\n\n" + "\n\n".join(filtered[:10])
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ *No results found for '{keyword}'.*", parse_mode='Markdown')

async def news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📰 தமிழ் செய்திகள்", callback_data='tamil_news')],
        [InlineKeyboardButton("🌍 English News", callback_data='english_news')],
        [InlineKeyboardButton("🏏 விளையாட்டு", callback_data='sports_news')],
        [InlineKeyboardButton("🎬 சினிமா", callback_data='cinema_news')],
        [InlineKeyboardButton("💰 பொருளாதாரம்", callback_data='business_news')],
        [InlineKeyboardButton("🔍 தேடு (Search)", callback_data='search_news')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "📰 *செய்தி வகைகள் - Select a category:*\n\n👇 கீழே உள்ள Button-ஐ அழுத்தவும்.",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    category = query.data
    
    if category == 'tamil_news':
        await get_news(update, context)
    elif category == 'english_news':
        english_news = get_english_news()
        if english_news:
            message = "🌍 *World News (English):*\n\n" + "\n\n".join(english_news[:8])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ English news unavailable.")
    elif category == 'search_news':
        await query.message.reply_text("🔍 Send /search <keyword> (e.g., /search தேர்தல்)")
    else:
        await query.message.reply_text(f"⏳ '{category}' category coming soon!")

async def auto_post_morning(app):
    users = get_all_users()
    if not users:
        return
    tamil_news = get_bbc_news() + get_dailythanthi_news()
    if tamil_news:
        message = "🌅 *Good Morning! Here's your Tamil News:*\n\n" + "\n\n".join(tamil_news[:8])
        for chat_id in users:
            try:
                await app.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                await asyncio.sleep(0.5)
            except:
                pass

async def auto_post_evening(app):
    users = get_all_users()
    if not users:
        return
    english_news = get_english_news()
    if english_news:
        message = "🌙 *Good Evening! Here's your English News:*\n\n" + "\n\n".join(english_news[:8])
        for chat_id in users:
            try:
                await app.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')
                await asyncio.sleep(0.5)
            except:
                pass

# ---------- MAIN ----------
def main():
    init_db()
    print("🤖 Multi-Source News Broadcast Bot இயங்குகிறது...")
    print(f"👥 Total users in DB: {get_user_count()}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", news_menu))
    app.add_handler(CommandHandler("news", get_news))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    scheduler = AsyncIOScheduler(timezone='Asia/Kolkata')
    scheduler.add_job(auto_post_morning, CronTrigger(hour=8, minute=0), args=[app])
    scheduler.add_job(auto_post_evening, CronTrigger(hour=18, minute=0), args=[app])
    scheduler.start()
    print("✅ Scheduler started! Auto-post at 8:00 AM & 6:00 PM IST")
    
    app.run_polling()

if __name__ == "__main__":
    main()
