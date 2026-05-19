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
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set!")

ADMIN_ID = int(os.environ.get("ADMIN_ID", 8623813419))

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

# ---------- BBC TAMIL NEWS ----------
def get_bbc_news():
    news_list = []
    # 1. BBC Tamil
    try:
        url = "https://www.bbc.com/tamil"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', class_='focusIndicatorDisplayBlock')
        if not articles:
            articles = soup.find_all('h3')
        for a in articles[:4]:
            title = a.get_text(strip=True)
            href = a.get('href') if a.name == 'a' else (a.find('a').get('href') if a.find('a') else None)
            if title and len(title) > 15 and href:
                if not href.startswith('http'):
                    href = 'https://www.bbc.com' + href
                news_list.append(f"📌 *{title}*\n🔗 [Read more]({href})\n🏷️ *Source:* BBC Tamil")
        print(f"✅ BBC Tamil - {len(news_list[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ BBC Tamil error: {e}")

    # 2. Daily Thanthi
    try:
        url = "https://www.dailythanthi.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        count = 0
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/news/' in href:
                title = a.get_text(strip=True)
                if title and len(title) > 20:
                    full_url = href if href.startswith('http') else 'https://www.dailythanthi.com' + href
                    news_list.append(f"📌 *{title}*\n🔗 [Read more]({full_url})\n🏷️ *Source:* தினத்தந்தி")
                    count += 1
                    if count >= 4:
                        break
        print(f"✅ Daily Thanthi - {count} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Daily Thanthi error: {e}")

    # 3. The Hindu Tamil RSS
    try:
        feed = feedparser.parse('https://www.thehindu.com/news/national/tamil-nadu/?service=rss')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* The Hindu Tamil")
        print(f"✅ The Hindu Tamil - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ The Hindu RSS error: {e}")

    # 4. Puthiya Thalaimurai RSS
    try:
        feed = feedparser.parse('https://www.puthiyathalaimurai.com/rss')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Puthiya Thalaimurai")
        print(f"✅ Puthiya Thalaimurai - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Puthiya Thalaimurai RSS error: {e}")

    if not news_list:
        news_list.append("📰 *தமிழ் செய்திகள்*\nஇப்போது செய்திகள் எதுவும் கிடைக்கவில்லை.")
    return news_list[:15]
# ---------- ENGLISH NEWS (BBC World) ----------
def get_english_news():
    news_list = []
    # 1. BBC World
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/news/world/rss.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC World")
        print(f"✅ BBC World - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ BBC World RSS error: {e}")

    # 2. Reuters World
    try:
        feed = feedparser.parse('http://feeds.reuters.com/reuters/worldNews')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Reuters")
        print(f"✅ Reuters World - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Reuters World RSS error: {e}")

    # 3. Al Jazeera
    try:
        feed = feedparser.parse('https://www.aljazeera.com/xml/rss/all.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Al Jazeera")
        print(f"✅ Al Jazeera - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Al Jazeera RSS error: {e}")

    # 4. The Guardian World
    try:
        feed = feedparser.parse('https://www.theguardian.com/world/rss')
        for entry in feed.entries[:4]:
            news_list.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* The Guardian")
        print(f"✅ The Guardian - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ The Guardian RSS error: {e}")

    if not news_list:
        news_list.append("🌍 *World News*\nNo news available. Please try again later.")
    return news_list[:15]
# ---------- DAILY THANTHI NEWS (Selenium + Fallback) ----------
def get_dailythanthi_news():
    news_list = []
    try:
        url = "https://www.dailythanthi.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for all links that contain '/news/'
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/news/' in href:
                title = a.get_text(strip=True)
                if title and len(title) > 20:
                    full_url = href if href.startswith('http') else 'https://www.dailythanthi.com' + href
                    news_list.append(f"📌 *{title}*\n🔗 [Read more]({full_url})\n🏷️ *Source:* தினத்தந்தி")
        print(f"✅ Daily Thanthi - {len(news_list)} செய்திகள்")
    except Exception as e:
        print(f"❌ Daily Thanthi error: {e}")
    return news_list[:10]

# ---------- SPORTS NEWS ----------
def get_sports_news():
    news_list = []
    # 1. BBC Sport
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/sport/rss.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC Sport")
        print(f"✅ BBC Sport - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ BBC Sport RSS error: {e}")

    # 2. Sky Sports
    try:
        feed = feedparser.parse('http://feeds.skynews.com/feeds/rss/sports.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Sky Sports")
        print(f"✅ Sky Sports - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Sky Sports RSS error: {e}")

    # 3. ESPN
    try:
        feed = feedparser.parse('https://www.espn.com/espn/rss/news')
        for entry in feed.entries[:4]:
            news_list.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* ESPN")
        print(f"✅ ESPN - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ ESPN RSS error: {e}")

    # 4. NYT Sports
    try:
        feed = feedparser.parse('https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* NYT Sports")
        print(f"✅ NYT Sports - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ NYT Sports RSS error: {e}")

    if not news_list:
        news_list.append("🏏 *Sports News*\nNo sports news available. Try again later.")
    return news_list[:15]
# ---------- CINEMA NEWS ----------
def get_cinema_news():
    news_list = []
    # 1. Variety
    try:
        feed = feedparser.parse('https://variety.com/feed/')
        for entry in feed.entries[:4]:
            news_list.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Variety")
        print(f"✅ Variety - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Variety RSS error: {e}")

    # 2. Hollywood Reporter
    try:
        feed = feedparser.parse('https://www.hollywoodreporter.com/feed/')
        for entry in feed.entries[:4]:
            news_list.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Hollywood Reporter")
        print(f"✅ Hollywood Reporter - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Hollywood Reporter RSS error: {e}")

    # 3. Empire Online
    try:
        feed = feedparser.parse('https://www.empireonline.com/feed/')
        for entry in feed.entries[:4]:
            news_list.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Empire")
        print(f"✅ Empire - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Empire RSS error: {e}")

    # 4. Deadline
    try:
        feed = feedparser.parse('https://deadline.com/feed/')
        for entry in feed.entries[:4]:
            news_list.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Deadline")
        print(f"✅ Deadline - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Deadline RSS error: {e}")

    if not news_list:
        news_list.append("🎬 *Cinema News*\nNo cinema news available. Try again later.")
    return news_list[:15]
# ---------- BUSINESS NEWS ----------
def get_business_news():
    news_list = []
    # 1. Reuters Business
    try:
        feed = feedparser.parse('http://feeds.reuters.com/reuters/businessNews')
        for entry in feed.entries[:4]:
            news_list.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Reuters")
        print(f"✅ Reuters Business - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Reuters RSS error: {e}")

    # 2. BBC Business
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/news/business/rss.xml')
        for entry in feed.entries[:4]:
            news_list.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC Business")
        print(f"✅ BBC Business - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ BBC Business RSS error: {e}")

    # 3. Bloomberg Markets
    try:
        feed = feedparser.parse('https://feeds.bloomberg.com/markets/news.rss')
        for entry in feed.entries[:4]:
            news_list.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Bloomberg")
        print(f"✅ Bloomberg Markets - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Bloomberg RSS error: {e}")

    # 4. Financial Times
    try:
        feed = feedparser.parse('https://www.ft.com/?format=rss')
        for entry in feed.entries[:4]:
            news_list.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Financial Times")
        print(f"✅ Financial Times - {len(feed.entries[:4])} செய்திகள்")
    except Exception as e:
        print(f"⚠️ Financial Times RSS error: {e}")

    if not news_list:
        news_list.append("💰 *Business News*\nNo business news available. Try again later.")
    return news_list[:15]
# ---------- SEARCH ----------
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
        except:
            fail_count += 1
    await status_msg.edit_text(
        f"✅ Broadcast முடிந்தது!\n\n"
        f"📨 வெற்றி: {success_count}\n"
        f"❌ தோல்வி: {fail_count}\n"
        f"👥 மொத்தம்: {len(users)}"
    )

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 செய்திகள் சேகரிக்கப்படுகிறது. சிறிது பொறுக்கவும்...")
    all_news = get_bbc_news() + get_dailythanthi_news()
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

# ---------- CATEGORY MENU ----------
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

# ---------- BUTTON HANDLER (FIXED: No get_news call) ----------
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data

    if category == 'tamil_news':
        await query.edit_message_text("📰 தமிழ் செய்திகள் சேகரிக்கப்படுகிறது. சிறிது பொறுக்கவும்...")
        all_news = get_bbc_news() + get_dailythanthi_news()
        if all_news:
            message = "📰 *பல தள செய்திகள்:*\n\n" + "\n\n".join(all_news[:15])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ எந்த தளத்திலிருந்தும் செய்திகள் கிடைக்கவில்லை.")
    elif category == 'english_news':
        await query.edit_message_text("🌍 English news fetching...")
        english_news = get_english_news()
        if english_news:
            message = "🌍 *World News (English):*\n\n" + "\n\n".join(english_news[:8])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ English news unavailable.")
    elif category == 'sports_news':
        await query.edit_message_text("🏏 Sports news fetching...")
        sports_news = get_sports_news()
        if sports_news and not sports_news[0].startswith("🏏 *Sports News*\\nUnable"):
            message = "🏏 *Sports News:*\n\n" + "\n\n".join(sports_news)
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("🏏 Sports news unavailable. Try again later.")
    elif category == 'cinema_news':
        await query.edit_message_text("🎬 Cinema news fetching...")
        cinema_news = get_cinema_news()
        if cinema_news and not cinema_news[0].startswith("🎬 *Cinema News*\\nUnable"):
            message = "🎬 *Cinema News:*\n\n" + "\n\n".join(cinema_news)
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("🎬 Cinema news unavailable. Try again later.")
    elif category == 'business_news':
        await query.edit_message_text("💰 Business news fetching...")
        business_news = get_business_news()
        if business_news and not business_news[0].startswith("💰 *Business News*\\nUnable"):
            message = "💰 *Business News:*\n\n" + "\n\n".join(business_news)
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("💰 Business news unavailable. Try again later.")
    elif category == 'search_news':
        await query.edit_message_text("🔍 *Search Feature*\n\nSend /search <keyword>\n\nExample: /search தேர்தல்", parse_mode='Markdown')
    else:
        await query.edit_message_text(f"⏳ '{category}' category coming soon!")

# ---------- AUTO-POST ----------
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

    # Run async
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def run():
        await app.bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook cleared.")

        scheduler = AsyncIOScheduler(timezone='Asia/Kolkata')
        scheduler.add_job(auto_post_morning, CronTrigger(hour=8, minute=0), args=[app])
        scheduler.add_job(auto_post_evening, CronTrigger(hour=18, minute=0), args=[app])
        scheduler.start()
        print("✅ Scheduler started! Auto-post at 8:00 AM & 6:00 PM IST")

        await app.initialize()
        await app.start()
        await app.updater.start_polling()

        try:
            await asyncio.get_event_loop().create_future()
        except:
            pass

    loop.run_until_complete(run())

if __name__ == "__main__":
    main()
