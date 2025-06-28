import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # বট টোকেন
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # অ্যাডমিন আইডি
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    
    # ডেটাবেস কনফিগ
    DB_NAME = os.getenv("DB_NAME", "earning_bot.db")
    
    # বাধ্যতামূলক চ্যানেল
    REQUIRED_CHANNELS = [channel.strip() for channel in os.getenv("REQUIRED_CHANNELS", "").split(",") if channel]
    
    # বট সেটিংস
    MIN_WITHDRAW = float(os.getenv("MIN_WITHDRAW", 100))
    MAX_WITHDRAW = float(os.getenv("MAX_WITHDRAW", 10000))
    TASK_COOLDOWN = int(os.getenv("TASK_COOLDOWN", 300))
    TASK_REWARD = float(os.getenv("TASK_REWARD", 10))
    
    # Web App URL
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-web-app.glitch.me")
    
    # পেমেন্ট মেথড সক্রিয়তা
    BKASH_ENABLED = os.getenv("BKASH_ENABLED", "True") == "True"
    CRYPTO_ENABLED = os.getenv("CRYPTO_ENABLED", "True") == "True"
    
    # ডিফল্ট ওয়ালেট ঠিকানা (এগুলো অ্যাডমিন প্যানেল থেকে পরিবর্তন করা যাবে)
    BKASH_MERCHANT_NO = os.getenv("BKASH_MERCHANT_NO", "0123456789")
    USDT_TRC20_WALLET = os.getenv("USDT_TRC20_WALLET", "TRxwXxXxXxXxXxXxXxXxXxXxXxXxX")
    TON_WALLET = os.getenv("TON_WALLET", "EQxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxXxX")
    DOGE_WALLET = os.getenv("DOGE_WALLET", "DxXxXxXxXxXxXxXxXxXxXxXxXxX")
    
    # পয়েন্ট রেট
    POINTS_RATE = {
        'bkash': 1.0,  # 1 টাকা = 1 পয়েন্ট
        'usdt': 100.0,  # 1 USDT = 100 পয়েন্ট
        'ton': 50.0,    # 1 TON = 50 পয়েন্ট
        'doge': 10.0    # 1 DOGE = 10 পয়েন্ট
    }
