print("🚀 Bot is starting...")

import os
import asyncio
import csv
import sqlite3
import requests
import feedparser
import json
from datetime import datetime
from bs4 import BeautifulSoup
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

# ---------- 1. TAMIL NEWS (BBC, Daily Thanthi, The Hindu, Dinamalar) ----------
def get_tamil_news():
    all_news = []
    # 1. BBC Tamil
    try:
        url = "https://www.bbc.com/tamil"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = soup.find_all('a', class_='focusIndicatorDisplayBlock')
        if not articles:
            articles = soup.find_all('h3')
        for a in articles[:5]:
            title = a.get_text(strip=True)
            href = a.get('href') if a.name == 'a' else (a.find('a').get('href') if a.find('a') else None)
            if title and len(title) > 15 and href:
                if not href.startswith('http'):
                    href = 'https://www.bbc.com' + href
                all_news.append(f"📌 *{title}*\n🔗 [Read more]({href})\n🏷️ *Source:* BBC Tamil")
    except Exception as e:
        print(f"⚠️ BBC Tamil error: {e}")

    # 2. Daily Thanthi
    try:
        url = "https://www.dailythanthi.com/"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/news/' in href:
                title = a.get_text(strip=True)
                if title and len(title) > 20:
                    full_url = href if href.startswith('http') else 'https://www.dailythanthi.com' + href
                    all_news.append(f"📌 *{title}*\n🔗 [Read more]({full_url})\n🏷️ *Source:* தினத்தந்தி")
                if len([n for n in all_news if 'தினத்தந்தி' in n]) >= 5:
                    break
    except Exception as e:
        print(f"⚠️ Daily Thanthi error: {e}")

    # 3. The Hindu Tamil (RSS)
    try:
        feed = feedparser.parse('https://www.thehindu.com/news/national/tamil-nadu/?service=rss')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* The Hindu Tamil")
    except Exception as e:
        print(f"⚠️ The Hindu Tamil error: {e}")

    # 4. Dinamalar (Alternative Tamil source)
    try:
        feed = feedparser.parse('https://www.dinamalar.com/rss/tamilnadu.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Dinamalar")
    except Exception as e:
        print(f"⚠️ Dinamalar error: {e}")

    if not all_news:
        all_news.append("📰 *தமிழ் செய்திகள்*\nஇப்போது செய்திகள் எதுவும் கிடைக்கவில்லை.")
    print(f"✅ Tamil News - {len(all_news)} செய்திகள்")
    return all_news[:12]

# ---------- 2. ENGLISH WORLD NEWS (BBC, Reuters, Guardian, Al Jazeera) ----------
def get_english_news():
    all_news = []
    # 1. BBC World
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/news/world/rss.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC World")
    except Exception as e:
        print(f"⚠️ BBC World error: {e}")

    # 2. Reuters World (Fixed URL)
    try:
        feed = feedparser.parse('http://feeds.reuters.com/reuters/worldNews')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Reuters")
    except Exception as e:
        print(f"⚠️ Reuters World error: {e}")

    # 3. The Guardian World
    try:
        feed = feedparser.parse('https://www.theguardian.com/world/rss')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* The Guardian")
    except Exception as e:
        print(f"⚠️ Guardian error: {e}")

    # 4. Al Jazeera
    try:
        feed = feedparser.parse('https://www.aljazeera.com/xml/rss/all.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"📌 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Al Jazeera")
    except Exception as e:
        print(f"⚠️ Al Jazeera error: {e}")

    if not all_news:
        all_news.append("🌍 *World News*\nNo news available at the moment.")
    print(f"✅ English News - {len(all_news)} செய்திகள்")
    return all_news[:12]

# ---------- 3. SPORTS NEWS (BBC, Sky Sports, ESPN, NYT Sports) ----------
def get_sports_news():
    all_news = []
    # 1. BBC Sport
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/sport/rss.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC Sport")
    except Exception as e:
        print(f"⚠️ BBC Sport error: {e}")

    # 2. Sky Sports
    try:
        feed = feedparser.parse('http://feeds.skynews.com/feeds/rss/sports.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Sky Sports")
    except Exception as e:
        print(f"⚠️ Sky Sports error: {e}")

    # 3. ESPN
    try:
        feed = feedparser.parse('https://www.espn.com/espn/rss/news')
        for entry in feed.entries[:5]:
            all_news.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* ESPN")
    except Exception as e:
        print(f"⚠️ ESPN error: {e}")

    # 4. NYT Sports
    try:
        feed = feedparser.parse('https://rss.nytimes.com/services/xml/rss/nyt/Sports.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"🏏 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* NYT Sports")
    except Exception as e:
        print(f"⚠️ NYT Sports error: {e}")

    if not all_news:
        all_news.append("🏏 *Sports News*\nUnable to fetch sports news. Try again later.")
    print(f"✅ Sports News - {len(all_news)} செய்திகள்")
    return all_news[:12]

# ---------- 4. BUSINESS NEWS (Reuters, BBC Business, Bloomberg, Financial Times) ----------
def get_business_news():
    all_news = []
    # 1. Reuters Business
    try:
        feed = feedparser.parse('http://feeds.reuters.com/reuters/businessNews')
        for entry in feed.entries[:5]:
            all_news.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Reuters")
    except Exception as e:
        print(f"⚠️ Reuters Business error: {e}")

    # 2. BBC Business
    try:
        feed = feedparser.parse('https://feeds.bbci.co.uk/news/business/rss.xml')
        for entry in feed.entries[:5]:
            all_news.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* BBC Business")
    except Exception as e:
        print(f"⚠️ BBC Business error: {e}")

    # 3. Bloomberg Markets
    try:
        feed = feedparser.parse('https://feeds.bloomberg.com/markets/news.rss')
        for entry in feed.entries[:5]:
            all_news.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Bloomberg")
    except Exception as e:
        print(f"⚠️ Bloomberg error: {e}")

    # 4. Financial Times
    try:
        feed = feedparser.parse('https://www.ft.com/?format=rss')
        for entry in feed.entries[:5]:
            all_news.append(f"💰 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Financial Times")
    except Exception as e:
        print(f"⚠️ FT error: {e}")

    if not all_news:
        all_news.append("💰 *Business News*\nNo business news available. Try again later.")
    print(f"✅ Business News - {len(all_news)} செய்திகள்")
    return all_news[:12]

# ---------- 5. CINEMA NEWS (Variety, Hollywood Reporter, Empire, Deadline) ----------
def get_cinema_news():
    all_news = []
    # 1. Variety
    try:
        feed = feedparser.parse('https://variety.com/feed/')
        for entry in feed.entries[:5]:
            all_news.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Variety")
    except Exception as e:
        print(f"⚠️ Variety error: {e}")

    # 2. Hollywood Reporter
    try:
        feed = feedparser.parse('https://www.hollywoodreporter.com/feed/')
        for entry in feed.entries[:5]:
            all_news.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Hollywood Reporter")
    except Exception as e:
        print(f"⚠️ Hollywood Reporter error: {e}")

    # 3. Empire Online
    try:
        feed = feedparser.parse('https://www.empireonline.com/feed/')
        for entry in feed.entries[:5]:
            all_news.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Empire")
    except Exception as e:
        print(f"⚠️ Empire error: {e}")

    # 4. Deadline
    try:
        feed = feedparser.parse('https://deadline.com/feed/')
        for entry in feed.entries[:5]:
            all_news.append(f"🎬 *{entry.title}*\n🔗 [Read more]({entry.link})\n🏷️ *Source:* Deadline")
    except Exception as e:
        print(f"⚠️ Deadline error: {e}")

    if not all_news:
        all_news.append("🎬 *Cinema News*\nNo cinema news available. Try again later.")
    print(f"✅ Cinema News - {len(all_news)} செய்திகள்")
    return all_news[:12]

# ---------- 6. WEATHER NEWS (Open-Meteo API - No API Key Required) ----------
def get_weather(city):
    try:
        # 1. Geocode the city name to get latitude and longitude
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_response = requests.get(geo_url, timeout=10)
        geo_data = geo_response.json()
        if not geo_data.get("results"):
            return f"❌ *Weather Unavailable*\nCould not find coordinates for '{city}'. Please check the city name."

        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        city_name = geo_data["results"][0]["name"]
        country = geo_data["results"][0].get("country", "")

        # 2. Get current weather
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=auto"
        weather_response = requests.get(weather_url, timeout=10)
        weather_data = weather_response.json()

        if "current_weather" not in weather_data:
            return f"❌ *Weather Unavailable*\nCould not fetch weather for '{city}'."

        current = weather_data["current_weather"]
        temp = current["temperature"]
        windspeed = current["windspeed"]
        weather_code = current.get("weathercode", 0)

        # Simple weather description based on weather code
        weather_codes = {
            0: "Clear sky",
            1: "Mainly clear",
            2: "Partly cloudy",
            3: "Overcast",
            45: "Fog",
            51: "Light drizzle",
            61: "Rain",
            71: "Snow fall",
            80: "Rain showers"
        }
        description = weather_codes.get(weather_code, "Unknown")

        # Format the message
        weather_msg = (
            f"🌦️ *Weather for {city_name}, {country}*\n"
            f"🌡️ *Temperature:* {temp}°C\n"
            f"💨 *Wind Speed:* {windspeed} km/h\n"
            f"☁️ *Condition:* {description}"
        )
        return weather_msg

    except Exception as e:
        print(f"⚠️ Weather error: {e}")
        return f"❌ *Weather Unavailable*\nAn error occurred while fetching weather for '{city}'. Please try again later."

# ---------- SEARCH (Tamil only, you can extend) ----------
def search_news(keyword):
    all_news = get_tamil_news()  # Search only in Tamil news for now
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
        "🌦️ /weather <city> - வானிலை தகவல்\n"
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
        "/weather <city> - வானிலை தகவல்\n"
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
    all_news = get_tamil_news()  # for /news command we show Tamil news
    if all_news:
        message = "📰 *தமிழ் செய்திகள்:*\n\n" + "\n\n".join(all_news[:12])
        await update.message.reply_text(message, parse_mode='Markdown')
    else:
        await update.message.reply_text("❌ செய்திகள் எதுவும் கிடைக்கவில்லை.")

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

# ---------- WEATHER COMMAND ----------
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if city name is provided
    if not context.args:
        await update.message.reply_text(
            "🌦️ *Usage:* /weather <city>\n\n"
            "Example: `/weather London` or `/weather Chennai`",
            parse_mode='Markdown'
        )
        return

    city = " ".join(context.args)
    await update.message.reply_text(f"🌦️ *Fetching weather for {city}...*", parse_mode='Markdown')

    # Get weather data
    weather_info = get_weather(city)
    await update.message.reply_text(weather_info, parse_mode='Markdown')

# ---------- CATEGORY MENU ----------
async def news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📰 தமிழ் செய்திகள்", callback_data='tamil_news')],
        [InlineKeyboardButton("🌍 English News", callback_data='english_news')],
        [InlineKeyboardButton("🏏 விளையாட்டு", callback_data='sports_news')],
        [InlineKeyboardButton("🎬 சினிமா", callback_data='cinema_news')],
        [InlineKeyboardButton("💰 பொருளாதாரம்", callback_data='business_news')],
        [InlineKeyboardButton("🌦️ வானிலை", callback_data='weather_news')],
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
        await query.edit_message_text("📰 தமிழ் செய்திகள் சேகரிக்கப்படுகிறது. சிறிது பொறுக்கவும்...")
        news = get_tamil_news()
        if news:
            message = "📰 *தமிழ் செய்திகள்:*\n\n" + "\n\n".join(news[:12])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ தமிழ் செய்திகள் எதுவும் கிடைக்கவில்லை.")
    elif category == 'english_news':
        await query.edit_message_text("🌍 English news fetching...")
        news = get_english_news()
        if news:
            message = "🌍 *World News (English):*\n\n" + "\n\n".join(news[:12])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("❌ English news unavailable.")
    elif category == 'sports_news':
        await query.edit_message_text("🏏 Sports news fetching...")
        news = get_sports_news()
        if news:
            message = "🏏 *Sports News:*\n\n" + "\n\n".join(news[:12])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("🏏 Sports news unavailable. Try again later.")
    elif category == 'cinema_news':
        await query.edit_message_text("🎬 Cinema news fetching...")
        news = get_cinema_news()
        if news:
            message = "🎬 *Cinema News:*\n\n" + "\n\n".join(news[:12])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("🎬 Cinema news unavailable. Try again later.")
    elif category == 'business_news':
        await query.edit_message_text("💰 Business news fetching...")
        news = get_business_news()
        if news:
            message = "💰 *Business News:*\n\n" + "\n\n".join(news[:12])
            await query.message.reply_text(message, parse_mode='Markdown')
        else:
            await query.message.reply_text("💰 Business news unavailable. Try again later.")
    elif category == 'weather_news':
        # For weather button, show usage instructions
        await query.edit_message_text(
            "🌦️ *Weather Feature*\n\n"
            "You can get current weather for any city using the `/weather` command.\n\n"
            "Example: `/weather Chennai` or `/weather New York`",
            parse_mode='Markdown'
        )
    elif category == 'search_news':
        await query.edit_message_text("🔍 *Search Feature*\n\nSend /search <keyword>\n\nExample: /search தேர்தல்", parse_mode='Markdown')
    else:
        await query.edit_message_text(f"⏳ '{category}' category coming soon!")

# ---------- AUTO-POST ----------
async def auto_post_morning(app):
    users = get_all_users()
    if not users:
        return
    tamil_news = get_tamil_news()
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
    app.add_handler(CommandHandler("weather", weather_command))  # New weather command
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))

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
