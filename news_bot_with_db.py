from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import csv
from datetime import datetime
import sqlite3
import asyncio

import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")   # Railway / Render variables-ல் stored  # உங்கள் Token

# ---------- DATABASE SETUP ----------
def init_db():
    """SQLite database - users ஐ சேமிக்க"""
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
    """புதிய user-ஐ database-ல் சேர்"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (chat_id, username, first_name, subscribed_date)
                 VALUES (?, ?, ?, ?)''', 
              (chat_id, username, first_name, datetime.now()))
    conn.commit()
    conn.close()

def get_all_users():
    """All users-ஐப் பெறு"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT chat_id FROM users")
    users = c.fetchall()
    conn.close()
    return [user[0] for user in users]

def get_user_count():
    """Total users count"""
    conn = sqlite3.connect('subscribers.db')
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

# ---------- TELEGRAM BOT HANDLERS ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Auto-subscribe: user-ஐ database-ல் சேர்
    add_user(user.id, user.username, user.first_name)
    
    await update.message.reply_text(
        f"வணக்கம் {user.first_name}! 👋\n\n"
        "நீங்கள் எங்கள் செய்திச் சேவையில் பதிவு செய்யப்பட்டுள்ளீர்கள்!\n\n"
        "📰 /news - உடனடியாக செய்திகளைப் பெற\n"
        "👥 /stats - மொத்த subscribers-களைப் பார்க்க (Admin only)\n"
        "📢 /broadcast [message] - அனைவருக்கும் செய்தி அனுப்ப (Admin only)\n"
        "/help - உதவி"
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-க்கு மட்டும் - Total subscribers count"""
    # உங்கள் Admin ID-ஐ இங்கே வைக்கவும்
    ADMIN_ID = 8623813419  # உங்கள் Telegram User ID-ஐ போடவும்
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ இந்தக் கட்டளையைப் பயன்படுத்த உங்களுக்கு அனுமதி இல்லை.")
        return
    
    count = get_user_count()
    await update.message.reply_text(f"👥 மொத்த subscribers: {count}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Admin-க்கு மட்டும் - All users-க்கும் message அனுப்ப"""
    ADMIN_ID = 8623813419  # உங்கள் Admin ID
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ இந்தக் கட்டளையைப் பயன்படுத்த உங்களுக்கு அனுமதி இல்லை.")
        return
    
    # /broadcast செய்தியை எடு
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
            await asyncio.sleep(0.05)  # Rate limit தவிர்க்க சிறிய delay
        except Exception as e:
            fail_count += 1
            print(f"Failed to send to {chat_id}: {e}")
    
    await status_msg.edit_text(
        f"✅ Broadcast முடிந்தது!\n\n"
        f"📨 வெற்றி: {success_count}\n"
        f"❌ தோல்வி: {fail_count}\n"
        f"👥 மொத்தம்: {len(users)}"
    )

async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """தினத்தந்தி செய்திகளைச் சேகரித்து அனுப்ப"""
    await update.message.reply_text("📰 செய்திகள் சேகரிக்கப்படுகிறது. சிறிது பொறுக்கவும்...")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    
    try:
        driver.get("https://www.dailythanthi.com/","https://www.thehindu.com/","https://www.dinamani.com/")
        driver.implicitly_wait(5)
        
        elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/news/')]")
        
        news_list = []
        for element in elements[:15]:  # முதல் 15 செய்திகள்
            title = element.text.strip()
            link = element.get_attribute('href')
            if title and len(title) > 20:
                news_list.append(f"📌 *{title}*\n🔗 [Read more]({link})")
        
        if news_list:
            message = "📰 *இன்றைய செய்திகள்:*\n\n" + "\n\n".join(news_list[:10])
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ இப்போது செய்திகள் எதுவும் கிடைக்கவில்லை.")
            
    except Exception as e:
        await update.message.reply_text(f"❌ பிழை: {e}")
    finally:
        driver.quit()

# ---------- MAIN ----------
def main():
    init_db()  # Database initialize
    
    print("🤖 News Broadcast Bot இயங்குகிறது...")
    print(f"👥 Total users in DB: {get_user_count()}")
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", get_news))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    app.run_polling()

if __name__ == "__main__":
    main()
