from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CallbackQueryHandler
from database import Database

db = Database()

async def handle_task_completion(update: Update, context: CallbackContext):
    # WebApp থেকে ডেটা প্রসেস করুন
    data = update.effective_message.web_app_data.data
    user_id = data.get('user_id')
    task_id = data.get('task_id')
    
    if not user_id or not task_id:
        return
    
    # টাস্ক সম্পন্ন করুন
    reward = db.complete_task(user_id, task_id)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"🎉 টাস্ক সম্পন্ন হয়েছে! আপনি {reward:.2f} পয়েন্ট পেয়েছেন।"
    )

def register_task_handlers(application):
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_task_completion))
