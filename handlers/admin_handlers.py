from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import Config
from database import Database

db = Database()

async def admin_wallet_management(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    settings = db.get_all_settings()
    
    text = (
        "💰 ওয়ালেট ব্যবস্থাপনা:\n\n"
        f"📱 বিকাশ সক্রিয়: {'✅' if settings.get('BKASH_ENABLED', '0') == '1' else '❌'}\n"
        f"📞 বিকাশ নম্বর: {settings.get('BKASH_MERCHANT_NO', 'সেট করা নেই')}\n\n"
        f"🪙 ক্রিপ্টো সক্রিয়: {'✅' if settings.get('CRYPTO_ENABLED', '0') == '1' else '❌'}\n"
        f"💳 USDT (TRC20): {settings.get('USDT_TRC20_WALLET', 'সেট করা নেই')}\n"
        f"⚡ TON: {settings.get('TON_WALLET', 'সেট করা নেই')}\n"
        f"🐕 DOGE: {settings.get('DOGE_WALLET', 'সেট করা নেই')}\n\n"
        "কোন সেটিং পরিবর্তন করতে চান?"
    )
    
    keyboard = [
        [InlineKeyboardButton("📱 বিকাশ সক্রিয়/নিষ্ক্রিয়", callback_data="admin_toggle_bkash")],
        [InlineKeyboardButton("📞 বিকাশ নম্বর পরিবর্তন", callback_data="admin_set_bkash_no")],
        [InlineKeyboardButton("🪙 ক্রিপ্টো সক্রিয়/নিষ্ক্রিয়", callback_data="admin_toggle_crypto")],
        [InlineKeyboardButton("💳 USDT ওয়ালেট পরিবর্তন", callback_data="admin_set_usdt_wallet")],
        [InlineKeyboardButton("⚡ TON ওয়ালেট পরিবর্তন", callback_data="admin_set_ton_wallet")],
        [InlineKeyboardButton("🐕 DOGE ওয়ালেট পরিবর্তন", callback_data="admin_set_doge_wallet")],
        [InlineKeyboardButton("🔙 অ্যাডমিন মেনু", callback_data="admin_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_toggle_bkash(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    current = db.get_setting('BKASH_ENABLED')
    new_value = '0' if current == '1' else '1'
    db.update_setting('BKASH_ENABLED', new_value)
    
    await query.edit_message_text(
        f"বিকাশ পেমেন্ট পদ্ধতি এখন {'সক্রিয় ✅' if new_value == '1' else 'নিষ্ক্রিয় ❌'} করা হয়েছে।",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ওয়ালেট ব্যবস্থাপনা", callback_data="admin_wallet_management")]
        ])
    )

async def admin_set_bkash_no(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"বর্তমান বিকাশ মার্চেন্ট নম্বর: {db.get_setting('BKASH_MERCHANT_NO')}\n\n"
        "নতুন বিকাশ মার্চেন্ট নম্বর লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_wallet_management")]
        ])
    )
    context.user_data['admin_action'] = 'set_bkash_no'

async def admin_toggle_crypto(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    current = db.get_setting('CRYPTO_ENABLED')
    new_value = '0' if current == '1' else '1'
    db.update_setting('CRYPTO_ENABLED', new_value)
    
    await query.edit_message_text(
        f"ক্রিপ্টো পেমেন্ট পদ্ধতি এখন {'সক্রিয় ✅' if new_value == '1' else 'নিষ্ক্রিয় ❌'} করা হয়েছে।",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ওয়ালেট ব্যবস্থাপনা", callback_data="admin_wallet_management")]
        ])
    )

async def admin_set_usdt_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"বর্তমান USDT (TRC20) ওয়ালেট: {db.get_setting('USDT_TRC20_WALLET')}\n\n"
        "নতুন USDT (TRC20) ওয়ালেট ঠিকানা লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_wallet_management")]
        ])
    )
    context.user_data['admin_action'] = 'set_usdt_wallet'

async def admin_set_ton_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"বর্তমান TON ওয়ালেট: {db.get_setting('TON_WALLET')}\n\n"
        "নতুন TON ওয়ালেট ঠিকানা লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_wallet_management")]
        ])
    )
    context.user_data['admin_action'] = 'set_ton_wallet'

async def admin_set_doge_wallet(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        f"বর্তমান DOGE ওয়ালেট: {db.get_setting('DOGE_WALLET')}\n\n"
        "নতুন DOGE ওয়ালেট ঠিকানা লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_wallet_management")]
        ])
    )
    context.user_data['admin_action'] = 'set_doge_wallet'

async def admin_process_wallet_settings(update: Update, context: CallbackContext):
    message = update.message
    admin_action = context.user_data.get('admin_action')
    
    if not admin_action:
        return
    
    new_value = message.text.strip()
    
    if admin_action == 'set_bkash_no':
        db.update_setting('BKASH_MERCHANT_NO', new_value)
        await message.reply_text(f"বিকাশ মার্চেন্ট নম্বর আপডেট করা হয়েছে: {new_value}")
    
    elif admin_action == 'set_usdt_wallet':
        db.update_setting('USDT_TRC20_WALLET', new_value)
        await message.reply_text(f"USDT (TRC20) ওয়ালেট ঠিকানা আপডেট করা হয়েছে: {new_value}")
    
    elif admin_action == 'set_ton_wallet':
        db.update_setting('TON_WALLET', new_value)
        await message.reply_text(f"TON ওয়ালেট ঠিকানা আপডেট করা হয়েছে: {new_value}")
    
    elif admin_action == 'set_doge_wallet':
        db.update_setting('DOGE_WALLET', new_value)
        await message.reply_text(f"DOGE ওয়ালেট ঠিকানা আপডেট করা হয়েছে: {new_value}")
    
    del context.user_data['admin_action']
    await admin_wallet_management(update, context)

async def admin_deposit_management(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    pending_deposits = db.get_pending_deposits()
    pending_count = len(pending_deposits) if pending_deposits else 0
    
    keyboard = [
        [InlineKeyboardButton(f"⏳ পেন্ডিং ডিপোজিট ({pending_count})", callback_data="admin_pending_deposits")],
        [InlineKeyboardButton("🔙 অ্যাডমিন মেনু", callback_data="admin_menu")]
    ]
    
    await query.edit_message_text(
        "ডিপোজিট ব্যবস্থাপনা:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_pending_deposits(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    deposits = db.get_pending_deposits()
    if not deposits:
        await query.edit_message_text(
            "কোন পেন্ডিং ডিপোজিট পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ডিপোজিট ব্যবস্থাপনা", callback_data="admin_deposit_management")]
            ])
        )
        return
    
    text = "⏳ পেন্ডিং ডিপোজিটের তালিকা:\n\n"
    for deposit in deposits[:10]:  # প্রথম ১০টি দেখাও
        user = db.get_user(deposit[1])
        username = f"@{user[1]}" if user and user[1] else f"User {deposit[1]}"
        
        method = deposit[3]
        if method == 'bkash':
            method_text = "📱 বিকাশ"
        elif method == 'crypto_usdt':
            method_text = "💳 USDT"
        elif method == 'crypto_ton':
            method_text = "⚡ TON"
        elif method == 'crypto_doge':
            method_text = "🐕 DOGE"
        else:
            method_text = method
        
        text += (
            f"🆔 {deposit[0]}\n"
            f"👤 {username}\n"
            f"📌 পদ্ধতি: {method_text}\n"
            f"💰 পরিমাণ: {deposit[2]:.2f} পয়েন্ট\n"
            f"📅 তারিখ: {deposit[6]}\n\n"
        )
    
    keyboard = []
    
    # প্রতিটি ডিপোজিটের জন্য অনুমোদন/বাতিল বাটন
    for deposit in deposits[:5]:  # প্রথম ৫টির জন্য বাটন দেখাও
        keyboard.append([
            InlineKeyboardButton(f"✅ {deposit[0]}", callback_data=f"approve_deposit_{deposit[0]}"),
            InlineKeyboardButton(f"❌ {deposit[0]}", callback_data=f"reject_deposit_{deposit[0]}")
        ])
    
    keyboard.append([InlineKeyboardButton("🔙 ডিপোজিট ব্যবস্থাপনা", callback_data="admin_deposit_management")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_approve_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    deposit_id = query.data.replace("approve_deposit_", "")
    deposit = db.get_deposit(deposit_id)
    
    if not deposit:
        await query.edit_message_text("ডিপোজিট আইডি পাওয়া যায়নি।")
        return
    
    db.update_deposit_status(deposit_id, 'completed')
    
    user = db.get_user(deposit[1])
    if user:
        try:
            await context.bot.send_message(
                chat_id=deposit[1],
                text=f"✅ আপনার ডিপোজিট অনুরোধ #{deposit_id} অনুমোদন করা হয়েছে। "
                     f"{deposit[2]:.2f} পয়েন্ট আপনার অ্যাকাউন্টে যোগ করা হয়েছে।"
            )
        except:
            pass
    
    await query.edit_message_text(
        f"ডিপোজিট #{deposit_id} অনুমোদন করা হয়েছে। ব্যবহারকারীর অ্যাকাউন্টে {deposit[2]:.2f} পয়েন্ট যোগ করা হয়েছে।",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 পেন্ডিং ডিপোজিট", callback_data="admin_pending_deposits")]
        ])
    )

async def admin_reject_deposit(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    deposit_id = query.data.replace("reject_deposit_", "")
    deposit = db.get_deposit(deposit_id)
    
    if not deposit:
        await query.edit_message_text("ডিপোজিট আইডি পাওয়া যায়নি।")
        return
    
    db.update_deposit_status(deposit_id, 'rejected')
    
    user = db.get_user(deposit[1])
    if user:
        try:
            await context.bot.send_message(
                chat_id=deposit[1],
                text=f"❌ আপনার ডিপোজিট অনুরোধ #{deposit_id} বাতিল করা হয়েছে। "
                     "আরও তথ্যের জন্য সাহায্য কেন্দ্রে যোগাযোগ করুন।"
            )
        except:
            pass
    
    await query.edit_message_text(
        f"ডিপোজিট #{deposit_id} বাতিল করা হয়েছে।",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 পেন্ডিং ডিপোজিট", callback_data="admin_pending_deposits")]
        ])
    )

# হ্যান্ডলার রেজিস্ট্রেশন ফাংশনে নতুন হ্যান্ডলার যোগ করুন
def register_admin_handlers(application):
    # পূর্বের সমস্ত হ্যান্ডলার
    # ...
    
    # নতুন ওয়ালেট এবং ডিপোজিট ব্যবস্থাপনা হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(admin_wallet_management, pattern="^admin_wallet_management$"))
    application.add_handler(CallbackQueryHandler(admin_toggle_bkash, pattern="^admin_toggle_bkash$"))
    application.add_handler(CallbackQueryHandler(admin_set_bkash_no, pattern="^admin_set_bkash_no$"))
    application.add_handler(CallbackQueryHandler(admin_toggle_crypto, pattern="^admin_toggle_crypto$"))
    application.add_handler(CallbackQueryHandler(admin_set_usdt_wallet, pattern="^admin_set_usdt_wallet$"))
    application.add_handler(CallbackQueryHandler(admin_set_ton_wallet, pattern="^admin_set_ton_wallet$"))
    application.add_handler(CallbackQueryHandler(admin_set_doge_wallet, pattern="^admin_set_doge_wallet$"))
    
    application.add_handler(CallbackQueryHandler(admin_deposit_management, pattern="^admin_deposit_management$"))
    application.add_handler(CallbackQueryHandler(admin_pending_deposits, pattern="^admin_pending_deposits$"))
    application.add_handler(CallbackQueryHandler(admin_approve_deposit, pattern="^approve_deposit_"))
    application.add_handler(CallbackQueryHandler(admin_reject_deposit, pattern="^reject_deposit_"))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, admin_process_wallet_settings))
    
    # পূর্বের সমস্ত হ্যান্ডলার
    # ...
