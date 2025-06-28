from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import Config
from database import Database
import random
import string
import time

db = Database()

# হেল্পার ফাংশন
def generate_deposit_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

async def show_deposit_methods(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = []
    
    if Config.BKASH_ENABLED and db.get_setting('BKASH_ENABLED') == '1':
        keyboard.append([InlineKeyboardButton("📱 বিকাশ (Bkash)", callback_data="deposit_bkash")])
    
    if Config.CRYPTO_ENABLED and db.get_setting('CRYPTO_ENABLED') == '1':
        keyboard.append([InlineKeyboardButton("🪙 ক্রিপ্টো (Crypto)", callback_data="deposit_crypto")])
    
    keyboard.append([InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")])
    
    if not keyboard:
        await query.edit_message_text(
            "বর্তমানে কোন ডিপোজিট পদ্ধতি সক্রিয় নেই। পরবর্তীতে আবার চেষ্টা করুন।",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]])
        )
        return
    
    await query.edit_message_text(
        "ডিপোজিট করার জন্য পেমেন্ট পদ্ধতি নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def deposit_bkash_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "বিকাশে ডিপোজিট করতে চাইলে নিচের পদক্ষেপগুলো অনুসরণ করুন:\n\n"
        "1. নিচের বিকাশ মার্চেন্ট নম্বরে টাকা পাঠান:\n"
        f"<code>{db.get_setting('BKASH_MERCHANT_NO')}</code>\n\n"
        "2. টাকার পরিমাণ লিখুন (টাকায়):",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 পেমেন্ট পদ্ধতি", callback_data="deposit_methods")]
        ]),
        parse_mode="HTML"
    )
    context.user_data['deposit_method'] = 'bkash'

async def deposit_crypto_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("USDT (TRC20)", callback_data="crypto_usdt")],
        [InlineKeyboardButton("TON", callback_data="crypto_ton")],
        [InlineKeyboardButton("DOGE", callback_data="crypto_doge")],
        [InlineKeyboardButton("🔙 পেমেন্ট পদ্ধতি", callback_data="deposit_methods")]
    ]
    
    await query.edit_message_text(
        "ক্রিপ্টোকারেন্সি নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def crypto_currency_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    crypto_type = query.data.replace("crypto_", "")
    context.user_data['deposit_method'] = f'crypto_{crypto_type}'
    
    await query.edit_message_text(
        f"{crypto_type.upper()} ডিপোজিট করতে চাইলে নিচের পদক্ষেপগুলো অনুসরণ করুন:\n\n"
        "1. নিচের ওয়ালেট ঠিকানায় ক্রিপ্টো পাঠান:\n"
        f"<code>{db.get_setting(f'{crypto_type.upper()}_WALLET')}</code>\n\n"
        f"2. {crypto_type.upper()} এর পরিমাণ লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ক্রিপ্টো নির্বাচন", callback_data="deposit_crypto")]
        ]),
        parse_mode="HTML"
    )

async def process_deposit_amount(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    deposit_method = context.user_data.get('deposit_method')
    
    if not deposit_method:
        return
    
    try:
        amount = float(message.text)
        
        if deposit_method == 'bkash':
            # টাকা থেকে পয়েন্ট কনভার্ট
            points = amount * Config.POINTS_RATE['bkash']
            payment_details = None
        elif deposit_method.startswith('crypto_'):
            crypto_type = deposit_method.split('_')[1]
            points = amount * Config.POINTS_RATE[crypto_type]
            payment_details = db.get_setting(f'{crypto_type.upper()}_WALLET')
        else:
            await message.reply_text("অবৈধ পেমেন্ট পদ্ধতি।")
            return
        
        deposit_id = generate_deposit_id()
        db.create_deposit_request(deposit_id, user_id, points, deposit_method, payment_details)
        
        if deposit_method == 'bkash':
            text = (
                f"📱 বিকাশ ডিপোজিট অনুরোধ তৈরি করা হয়েছে!\n\n"
                f"🆔 ডিপোজিট আইডি: <code>{deposit_id}</code>\n"
                f"💰 পরিমাণ: {amount:.2f} টাকা ({points:.2f} পয়েন্ট)\n"
                f"📞 বিকাশ নম্বর: <code>{db.get_setting('BKASH_MERCHANT_NO')}</code>\n\n"
                "পেমেন্ট করার সময় রেফারেন্স হিসেবে ডিপোজিট আইডি ব্যবহার করুন।\n"
                "পেমেন্ট সম্পন্ন হলে, TrxID এই চ্যাটে পাঠান।"
            )
        else:
            crypto_type = deposit_method.split('_')[1]
            text = (
                f"🪙 {crypto_type.upper()} ডিপোজিট অনুরোধ তৈরি করা হয়েছে!\n\n"
                f"🆔 ডিপোজিট আইডি: <code>{deposit_id}</code>\n"
                f"💰 পরিমাণ: {amount:.2f} {crypto_type.upper()} ({points:.2f} পয়েন্ট)\n"
                f"📌 ওয়ালেট: <code>{db.get_setting(f'{crypto_type.upper()}_WALLET')}</code>\n\n"
                "পেমেন্ট সম্পন্ন হলে, ট্রানজেকশন হ্যাশ (TxID) এই চ্যাটে পাঠান।"
            )
        
        keyboard = [
            [InlineKeyboardButton("📤 TxID/TrxID জমা দিন", callback_data=f"submit_payment_{deposit_id}")],
            [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
        ]
        
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML"
        )
        
        # অ্যাডমিনদের নোটিফাই করুন
        user = db.get_user(user_id)
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"নতুন ডিপোজিট অনুরোধ:\n\n"
                         f"ব্যবহারকারী: @{user[1]} ({user_id})\n"
                         f"পদ্ধতি: {deposit_method}\n"
                         f"পরিমাণ: {amount:.2f} ({points:.2f} পয়েন্ট)\n"
                         f"ডিপোজিট আইডি: {deposit_id}"
                )
            except:
                continue
        
        del context.user_data['deposit_method']
    except ValueError:
        await message.reply_text("দুঃখিত, দয়া করে একটি বৈধ সংখ্যা লিখুন।")

async def submit_payment_proof(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    deposit_id = query.data.replace("submit_payment_", "")
    context.user_data['deposit_id'] = deposit_id
    
    deposit = db.get_deposit(deposit_id)
    if not deposit:
        await query.edit_message_text("ডিপোজিট তথ্য পাওয়া যায়নি।")
        return
    
    method = deposit[3]
    
    if method == 'bkash':
        text = "আপনার বিকাশ TrxID লিখুন:"
    else:
        text = "আপনার ট্রানজেকশন হ্যাশ (TxID) লিখুন:"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="deposit_methods")]
        ])
    )

async def process_payment_proof(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    deposit_id = context.user_data.get('deposit_id')
    
    if not deposit_id:
        return
    
    txid = message.text.strip()
    deposit = db.get_deposit(deposit_id)
    
    if not deposit or deposit[1] != user_id:
        await message.reply_text("ত্রুটি: ডিপোজিট তথ্য পাওয়া যায়নি।")
        return
    
    db.update_deposit_status(deposit_id, 'pending', txid)
    
    await message.reply_text(
        "✅ আপনার পেমেন্ট প্রমাণ সফলভাবে জমা দেওয়া হয়েছে। "
        "আমাদের টিম এটি যাচাই করার পর আপনার অ্যাকাউন্টে পয়েন্ট যোগ করা হবে।"
    )
    
    # অ্যাডমিনদের নোটিফাই করুন
    user = db.get_user(user_id)
    for admin_id in Config.ADMIN_IDS:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=f"নতুন পেমেন্ট প্রমাণ জমা দেওয়া হয়েছে:\n\n"
                     f"ব্যবহারকারী: @{user[1]} ({user_id})\n"
                     f"ডিপোজিট আইডি: {deposit_id}\n"
                     f"পদ্ধতি: {deposit[3]}\n"
                     f"TxID/TrxID: {txid}\n\n"
                     f"অনুমোদন করতে: /admin"
            )
        except:
            continue
    
    del context.user_data['deposit_id']
    await show_main_menu(update, context)

# হ্যান্ডলার রেজিস্ট্রেশন ফাংশনে নতুন হ্যান্ডলার যোগ করুন
def register_user_handlers(application):
    # পূর্বের সমস্ত হ্যান্ডলার
    # ...
    
    # নতুন ডিপোজিট সম্পর্কিত হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(show_deposit_methods, pattern="^deposit_methods$"))
    application.add_handler(CallbackQueryHandler(deposit_bkash_handler, pattern="^deposit_bkash$"))
    application.add_handler(CallbackQueryHandler(deposit_crypto_handler, pattern="^deposit_crypto$"))
    application.add_handler(CallbackQueryHandler(crypto_currency_selected, pattern="^crypto_"))
    application.add_handler(CallbackQueryHandler(submit_payment_proof, pattern="^submit_payment_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_deposit_amount))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_payment_proof))
    
    # পূর্বের সমস্ত হ্যান্ডলার
    # ...
