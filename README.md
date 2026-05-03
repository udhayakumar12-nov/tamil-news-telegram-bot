# 📰 Tamil News Telegram Bot

A powerful Telegram bot that scrapes and delivers the latest Tamil news from **BBC Tamil** and **Daily Thanthi** directly to your phone. Perfect for staying updated with current affairs in Tamil!

## ✨ Features

- 🤖 **Multi-Source News**: Fetches news from **BBC Tamil** (via Requests/BeautifulSoup) and **Daily Thanthi** (via Selenium).
- 📢 **Broadcast System**: Admin can send messages to all subscribers at once.
- 👥 **Subscriber Management**: Uses SQLite to manage users who interact with the bot.
- ⚡ **Asynchronous**: Built with Python's `asyncio` for fast and non-blocking operations.
- 📁 **CSV Export**: Optionally saves fetched news to CSV files.

## 🛠️ Tech Stack

- **Language**: Python 3.14
- **Core Library**: `python-telegram-bot` (v21.x)
- **Web Scraping**: `requests`, `beautifulsoup4`, `selenium`
- **Database**: `sqlite3`
- **Automation**: `webdriver-manager`

## 📱 Bot Commands

| Command | Description | Access |
| :--- | :--- | :--- |
| `/start` | Subscribes you to the news service. | Public |
| `/news` | Fetches and sends the latest news instantly. | Public |
| `/stats` | Shows the total number of subscribers. | Admin Only |
| `/broadcast <message>` | Sends a message to all subscribers. | Admin Only |
| `/help` | Shows this help message. | Public |

## 🚀 How to Run Locally

Follow these steps to run the bot on your own computer:

### 1. Clone the Repository
```bash
git clone https://github.com/udhayakumar12-nov/tamil-news-telegram-bot.git
cd tamil-news-telegram-bot
