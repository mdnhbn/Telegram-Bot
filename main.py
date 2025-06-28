from telegram.ext import ApplicationBuilder
from config import Config
from handlers.user_handlers import register_user_handlers
from handlers.admin_handlers import register_admin_handlers
from handlers.task_handlers import register_task_handlers
import logging

# লগিং কনফিগার করুন
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def main():
    # বট অ্যাপ্লিকেশন তৈরি করুন
    application = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    
    # হ্যান্ডলার রেজিস্টার করুন
    register_user_handlers(application)
    register_admin_handlers(application)
    register_task_handlers(application)
    
    # বট চালু করুন
    application.run_polling()

if __name__ == '__main__':
    main()
