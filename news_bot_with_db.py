import os
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

# Temporary Hardcode (Replace with your actual token)
BOT_TOKEN = "8553083543:AAFH0mrb0fRgcQTYzDnH0xQPklz_BGmQQcw"
ADMIN_ID = 8623813419  # Your Telegram User ID

# Comment or remove the os.getenv line
# BOT_TOKEN = os.environ.get("BOT_TOKEN")