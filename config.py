import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # বট টোকেন
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # অ্যাডমিন আইডি (একাধিক অ্যাডমিনের জন্য কমা দিয়ে আলাদা করুন)
    ADMIN_IDS = [int(id) for id in os.getenv("ADMIN_IDS", "").split(",") if id]
    
    # ডেটাবেস কনফিগ
    DB_NAME = os.getenv("DB_NAME", "earning_bot.db")
    
    # বাধ্যতামূলক চ্যানেল (চ্যানেল ইউজারনেম বা আইডি)
    REQUIRED_CHANNELS = [channel.strip() for channel in os.getenv("REQUIRED_CHANNELS", "").split(",") if channel]
    
    # ক্রিপ্টো ওয়ালেট ঠিকানা
    CRYPTO_WALLET = os.getenv("CRYPTO_WALLET", "TRxwXxXxXxXxXxXxXxXxXxXxXxXxX")
    
    # বট সেটিংস
    MIN_WITHDRAW = float(os.getenv("MIN_WITHDRAW", 100))
    MAX_WITHDRAW = float(os.getenv("MAX_WITHDRAW", 10000))
    TASK_COOLDOWN = int(os.getenv("TASK_COOLDOWN", 300))  # সেকেন্ডে
    TASK_REWARD = float(os.getenv("TASK_REWARD", 10))
    
    # Web App URL (Glitch বা অন্য কোনো হোস্টে আপলোড করার পর এখানে URL দিন)
    WEB_APP_URL = os.getenv("WEB_APP_URL", "https://your-web-app.glitch.me")
