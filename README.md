# 📰 Tamil News Telegram Bot – NewsMinute

A powerful multilingual news aggregator bot that delivers the latest news from **15+ global and Tamil sources** directly to your Telegram.  
Get Tamil, English, Sports, Business, Cinema, Climate, and Weather news – all in one place.

**Bot Link:** [@newsminute_bot](https://t.me/newsminute_bot)

---

## ✨ Features

- 📰 **Tamil News** – BBC Tamil, Daily Thanthi, The Hindu Tamil, Dinamalar, News18 Tamil  
- 🌍 **English World News** – BBC World, Reuters, The Guardian, Al Jazeera  
- 🏏 **Sports News** – BBC Sport, Sky Sports, ESPN, NYT Sports  
- 🎬 **Cinema News** – Variety, Hollywood Reporter, Empire, Deadline  
- 💰 **Business News** – Reuters Business, BBC Business, Bloomberg, Financial Times  
- 🌍 **Climate & Environment** – BBC Climate, Guardian Environment, Reuters Environment  
- 🌀 **Weather & Disasters** – Reuters Natural Disasters, BBC Science (filtered)  
- 🌦️ **Live Weather** – Current temperature, wind speed, conditions for any city (powered by Open‑Meteo)  
- 🔍 **Search News** – Search within Tamil news  
- 📢 **Admin Broadcast** – Send messages to all subscribers  
- ⏰ **Auto‑post** – Tamil news at 8 AM IST, English news at 6 PM IST  
- 💾 **Subscriber Database** – SQLite stores users who start the bot  

---

## 🛠️ Tech Stack

- **Python 3.11+**
- `python-telegram-bot` (async polling)
- `requests`, `BeautifulSoup` (web scraping)
- `feedparser` (RSS)
- `APScheduler` (auto‑post)
- `sqlite3` (database)
- **Open‑Meteo API** (weather, no API key needed)
- **Railway** (hosting, 24/7)
- **Docker** (with Chrome for fallback scraping)

---

## 📱 Bot Commands

| Command | Description |
| :--- | :--- |
| `/start` | Subscribe to the service |
| `/menu` | Show category buttons |
| `/news` | Get latest Tamil news |
| `/weather <city>` | Current weather for any city |
| `/search <keyword>` | Search Tamil news |
| `/stats` | Total subscribers (Admin only) |
| `/broadcast <msg>` | Send message to all (Admin only) |
| `/help` | Help menu |

---

## 🚀 Run Your Own Instance

### Prerequisites

- Python 3.11 or higher
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Railway / Render / any cloud platform (or local machine)

### Local Setup

```bash
git clone https://github.com/udhayakumar12-nov/tamil-news-telegram-bot.git
cd tamil-news-telegram-bot
pip install -r requirements.txt
