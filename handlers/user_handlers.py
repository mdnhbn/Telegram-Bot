from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, WebAppInfo
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from config import Config
from database import Database
import random
import string
import time

db = Database()

# হেল্পার ফাংশন
async def check_channels_subscription(user_id, context: CallbackContext):
    if not Config.REQUIRED_CHANNELS:
        return True
    
    for channel in Config.REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=channel, user_id=user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            print(f"Error checking channel subscription: {e}")
            return False
    return True

def generate_deposit_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# কমান্ড হ্যান্ডলার
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    message = update.message
    
    # ডেটাবেসে ব্যবহারকারী যোগ করুন
    db.add_user(user.id, user.username, user.first_name, user.last_name)
    
    # চ্যানেল সাবস্ক্রিপশন চেক করুন
    is_subscribed = await check_channels_subscription(user.id, context)
    
    if not is_subscribed:
        # চ্যানেল জয়েন করার জন্য বাটন তৈরি করুন
        keyboard = []
        for channel in Config.REQUIRED_CHANNELS:
            try:
                chat = await context.bot.get_chat(channel)
                keyboard.append([InlineKeyboardButton(
                    text=f"জয়েন করুন {chat.title}", 
                    url=f"https://t.me/{chat.username}" if chat.username else chat.invite_link
                )])
            except:
                continue
        
        keyboard.append([InlineKeyboardButton("আমি জয়েন করেছি ✅", callback_data="check_subscription")])
        
        await message.reply_text(
            "বট ব্যবহার করতে নিচের চ্যানেলগুলোতে জয়েন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # ওয়ালেট সেট করা আছে কিনা চেক করুন
    user_data = db.get_user(user.id)
    if not user_data[5]:  # wallet_address
        await message.reply_text(
            "ট্রানজেকশনের জন্য আপনার ওয়ালেট ঠিকানা সেট করুন। নিচের বাটনে ক্লিক করে আপনার পেমেন্ট মেথড নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("ওয়ালেট সেট করুন", callback_data="set_wallet")
            ]])
        )
        return
    
    # ভেরিফিকেশন সম্পূর্ণ হলে মূল মেনু দেখান
    await show_main_menu(update, context)

async def check_subscription_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    is_subscribed = await check_channels_subscription(query.from_user.id, context)
    
    if is_subscribed:
        db.verify_user(query.from_user.id)
        await query.edit_message_text("ধন্যবাদ! আপনি এখন বট ব্যবহার করতে পারেন।")
        await show_main_menu_from_query(query, context)
    else:
        await query.answer("আপনি এখনও সব চ্যানেলে জয়েন করেননি। দয়া করে সব চ্যানেলে জয়েন করুন এবং আবার চেষ্টা করুন।", show_alert=True)

async def set_wallet_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("বিকাশ", callback_data="wallet_bkash")],
        [InlineKeyboardButton("নগদ", callback_data="wallet_nagad")],
        [InlineKeyboardButton("রকেট", callback_data="wallet_rocket")],
        [InlineKeyboardButton("ক্রিপ্টো (USDT TRC20)", callback_data="wallet_crypto")],
    ]
    
    await query.edit_message_text(
        "পেমেন্ট গ্রহণের জন্য আপনার পছন্দের ওয়ালেট নির্বাচন করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def wallet_type_selected(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    wallet_type = query.data.replace("wallet_", "")
    context.user_data['wallet_type'] = wallet_type
    
    await query.edit_message_text(
        f"আপনার {wallet_type.upper()} ওয়ালেট ঠিকানা পাঠান:"
    )

async def save_wallet_address(update: Update, context: CallbackContext):
    message = update.message
    wallet_address = message.text
    wallet_type = context.user_data.get('wallet_type')
    
    if wallet_type and wallet_address:
        db.update_user_wallet(message.from_user.id, wallet_address, wallet_type)
        db.verify_user(message.from_user.id)
        await message.reply_text("আপনার ওয়ালেট ঠিকানা সফলভাবে সংরক্ষণ করা হয়েছে!")
        await show_main_menu(update, context)
    else:
        await message.reply_text("দুঃখিত, একটি ত্রুটি হয়েছে। দয়া করে আবার চেষ্টা করুন।")

async def show_main_menu(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("💰 টাস্ক করুন", callback_data="tasks")],
        [InlineKeyboardButton("📣 বিজ্ঞাপন দিন", callback_data="ads")],
        [InlineKeyboardButton("👤 আমার অ্যাকাউন্ট", callback_data="account")],
        [InlineKeyboardButton("💵 উইথড্র", callback_data="withdraw")],
        [InlineKeyboardButton("🔗 রেফারেল", callback_data="referral")],
    ]
    
    await message.reply_text(
        "প্রধান মেনু:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_main_menu_from_query(query, context: CallbackContext):
    user_id = query.from_user.id
    
    keyboard = [
        [InlineKeyboardButton("💰 টাস্ক করুন", callback_data="tasks")],
        [InlineKeyboardButton("📣 বিজ্ঞাপন দিন", callback_data="ads")],
        [InlineKeyboardButton("👤 আমার অ্যাকাউন্ট", callback_data="account")],
        [InlineKeyboardButton("💵 উইথড্র", callback_data="withdraw")],
        [InlineKeyboardButton("🔗 রেফারেল", callback_data="referral")],
    ]
    
    await query.edit_message_text(
        "প্রধান মেনু:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_account(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    if not user:
        await query.edit_message_text("ব্যবহারকারী তথ্য পাওয়া যায়নি।")
        return
    
    balance = user[7]
    total_earned = user[8]
    referral_count = user[9]
    referral_earnings = user[10]
    wallet_type = user[6]
    wallet_address = user[5]
    
    text = (
        f"👤 আপনার অ্যাকাউন্ট তথ্য:\n\n"
        f"💰 বর্তমান ব্যালেন্স: {balance:.2f} পয়েন্ট\n"
        f"💵 মোট আয়: {total_earned:.2f} পয়েন্ট\n"
        f"👥 রেফারেল: {referral_count} জন (আয়: {referral_earnings:.2f} পয়েন্ট)\n"
        f"💳 ওয়ালেট: {wallet_type.upper() if wallet_type else 'সেট করা নেই'}\n"
        f"📌 ঠিকানা: {wallet_address if wallet_address else 'সেট করা নেই'}"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")],
        [InlineKeyboardButton("✏️ ওয়ালেট পরিবর্তন", callback_data="set_wallet")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_tasks_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    tasks = db.get_active_tasks()
    if not tasks:
        await query.edit_message_text(
            "বর্তমানে কোন টাস্ক পাওয়া যায়নি। পরবর্তীতে আবার চেষ্টা করুন।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
            ])
        )
        return
    
    # শেষ টাস্ক সম্পন্ন করার সময় চেক করুন
    last_task_time = db.get_user_last_task_time(query.from_user.id)
    if last_task_time:
        current_time = time.time()
        last_time = time.mktime(time.strptime(last_task_time, "%Y-%m-%d %H:%M:%S"))
        cooldown_remaining = Config.TASK_COOLDOWN - (current_time - last_time)
        
        if cooldown_remaining > 0:
            minutes = int(cooldown_remaining // 60)
            seconds = int(cooldown_remaining % 60)
            await query.edit_message_text(
                f"আপনি পরবর্তী টাস্ক করতে পারবেন {minutes} মিনিট {seconds} সেকেন্ড পর।",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
                ])
            )
            return
    
    # Web App বাটন সহ টাস্ক মেনু দেখান
    task = tasks[0]  # প্রথম টাস্কটি দেখান (আপনি র্যান্ডম বা অন্য কোনো লজিক ব্যবহার করতে পারেন)
    web_app_url = f"{Config.WEB_APP_URL}?task_id={task[0]}&user_id={query.from_user.id}"
    
    keyboard = [
        [InlineKeyboardButton(
            "টাস্ক শুরু করুন",
            web_app=WebAppInfo(url=web_app_url)
        )],
        [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        f"🎯 টাস্ক: {task[1]}\n\n"
        f"📝 বিবরণ: {task[2]}\n\n"
        f"💰 পুরস্কার: {task[4]:.2f} পয়েন্ট",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def complete_task_from_webapp(update: Update, context: CallbackContext):
    # WebApp ডেটা প্রসেস করুন
    data = json.loads(update.effective_message.web_app_data.data)
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

async def show_withdraw_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    if not user or not user[5]:  # wallet_address
        await query.edit_message_text(
            "উইথড্র করার জন্য আপনাকে প্রথমে আপনার ওয়ালেট ঠিকানা সেট করতে হবে।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("ওয়ালেট সেট করুন", callback_data="set_wallet")],
                [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
            ])
        )
        return
    
    balance = user[7]
    wallet_type = user[6]
    wallet_address = user[5]
    
    text = (
        f"💵 উইথড্র অনুরোধ\n\n"
        f"💰 আপনার ব্যালেন্স: {balance:.2f} পয়েন্ট\n"
        f"💳 ওয়ালেট: {wallet_type.upper()}\n"
        f"📌 ঠিকানা: {wallet_address}\n\n"
        f"সর্বনিম্ন উইথড্র: {Config.MIN_WITHDRAW:.2f} পয়েন্ট\n"
        f"সর্বোচ্চ উইথড্র: {Config.MAX_WITHDRAW:.2f} পয়েন্ট\n\n"
        f"উইথড্র করার পরিমাণ লিখুন:"
    )
    
    await query.edit_message_text(text)
    context.user_data['awaiting_withdraw_amount'] = True

async def process_withdraw_amount(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    
    if not context.user_data.get('awaiting_withdraw_amount'):
        return
    
    try:
        amount = float(message.text)
        user = db.get_user(user_id)
        balance = user[7]
        
        if amount < Config.MIN_WITHDRAW:
            await message.reply_text(
                f"ত্রুটি: সর্বনিম্ন উইথড্র পরিমাণ {Config.MIN_WITHDRAW:.2f} পয়েন্ট।"
            )
            return
        elif amount > Config.MAX_WITHDRAW:
            await message.reply_text(
                f"ত্রুটি: সর্বোচ্চ উইথড্র পরিমাণ {Config.MAX_WITHDRAW:.2f} পয়েন্ট।"
            )
            return
        elif amount > balance:
            await message.reply_text(
                "ত্রুটি: আপনার পর্যাপ্ত ব্যালেন্স নেই।"
            )
            return
        
        # উইথড্র অনুরোধ তৈরি করুন
        wallet_address = user[5]
        db.create_withdrawal(user_id, amount, wallet_address)
        
        await message.reply_text(
            f"✅ {amount:.2f} পয়েন্ট উইথড্র করার অনুরোধ তৈরি করা হয়েছে। "
            f"আপনার {user[6].upper()} ওয়ালেটে ({wallet_address}) 24 ঘন্টার মধ্যে পেমেন্ট করা হবে।\n\n"
            "আপনার লেনদেনের ইতিহাস দেখতে 'আমার অ্যাকাউন্ট' এ যান।"
        )
        
        # অ্যাডমিনদের নোটিফাই করুন
        for admin_id in Config.ADMIN_IDS:
            try:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=f"নতুন উইথড্র অনুরোধ:\n\n"
                         f"ব্যবহারকারী: @{user[1]} ({user_id})\n"
                         f"পরিমাণ: {amount:.2f} পয়েন্ট\n"
                         f"ওয়ালেট: {user[6].upper()} ({wallet_address})"
                )
            except:
                continue
        
        del context.user_data['awaiting_withdraw_amount']
        await show_main_menu(update, context)
    except ValueError:
        await message.reply_text("দুঃখিত, দয়া করে একটি বৈধ সংখ্যা লিখুন।")

async def show_referral_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    if not user:
        return
    
    referral_count = user[9]
    referral_earnings = user[10]
    referral_link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
    
    text = (
        f"👥 রেফারেল প্রোগ্রাম\n\n"
        f"আপনি এখন পর্যন্ত {referral_count} জনকে রেফার করেছেন এবং {referral_earnings:.2f} পয়েন্ট অর্জন করেছেন।\n\n"
        f"আপনার রেফারেল লিঙ্ক:\n{referral_link}\n\n"
        f"আপনার লিঙ্ক শেয়ার করুন এবং প্রতিটি সফল রেফারেলের জন্য পুরস্কার পান!"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_ads_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    user = db.get_user(query.from_user.id)
    if not user:
        return
    
    text = "📣 বিজ্ঞাপন প্ল্যাটফর্ম\n\nআপনি যা করতে পারেন:"
    
    keyboard = [
        [InlineKeyboardButton("🆕 নতুন বিজ্ঞাপন তৈরি করুন", callback_data="create_ad")],
        [InlineKeyboardButton("📊 আমার বিজ্ঞাপন", callback_data="my_ads")],
        [InlineKeyboardButton("💳 পয়েন্ট কিনুন", callback_data="buy_points")],
        [InlineKeyboardButton("🔙 মূল মেনু", callback_data="main_menu")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_my_ads(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    ads = db.get_user_ads(query.from_user.id)
    if not ads:
        await query.edit_message_text(
            "আপনার কোন বিজ্ঞাপন পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🆕 নতুন বিজ্ঞাপন তৈরি করুন", callback_data="create_ad")],
                [InlineKeyboardButton("🔙 বিজ্ঞাপন মেনু", callback_data="ads")]
            ])
        )
        return
    
    text = "📊 আপনার বিজ্ঞাপন:\n\n"
    for ad in ads:
        status = "✅ সম্পূর্ণ" if ad[7] == 'completed' else "🚀 চলমান" if ad[7] == 'active' else "⏳ পেন্ডিং"
        text += (
            f"📌 {ad[2]}\n"
            f"🔗 লিঙ্ক: {ad[4]}\n"
            f"👁️‍🗨️ ভিউ: {ad[6]}/{ad[5]}\n"
            f"💵 খরচ: {ad[8]:.2f} পয়েন্ট\n"
            f"📅 তারিখ: {ad[9]}\n"
            f"🔄 অবস্থা: {status}\n\n"
        )
    
    keyboard = [
        [InlineKeyboardButton("🆕 নতুন বিজ্ঞাপন তৈরি করুন", callback_data="create_ad")],
        [InlineKeyboardButton("🔙 বিজ্ঞাপন মেনু", callback_data="ads")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def create_ad_step1(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "বিজ্ঞাপনের শিরোনাম লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বিজ্ঞাপন মেনু", callback_data="ads")]
        ])
    )
    context.user_data['ad_creation'] = {'step': 1}

async def process_ad_creation(update: Update, context: CallbackContext):
    message = update.message
    user_id = message.from_user.id
    
    if 'ad_creation' not in context.user_data:
        return
    
    step = context.user_data['ad_creation']['step']
    text = message.text
    
    if step == 1:
        context.user_data['ad_creation']['title'] = text
        context.user_data['ad_creation']['step'] = 2
        
        await message.reply_text(
            "বিজ্ঞাপনের বিবরণ লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="ads")]
            ])
        )
    elif step == 2:
        context.user_data['ad_creation']['description'] = text
        context.user_data['ad_creation']['step'] = 3
        
        await message.reply_text(
            "বিজ্ঞাপনের টার্গেট URL লিখুন (যে লিঙ্কে ক্লিক করলে ব্যবহারকারীরা যাবে):",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="ads")]
            ])
        )
    elif step == 3:
        if not text.startswith(('http://', 'https://')):
            await message.reply_text("দয়া করে একটি বৈধ URL লিখুন (http:// বা https:// দিয়ে শুরু করতে হবে)।")
            return
        
        context.user_data['ad_creation']['target_url'] = text
        context.user_data['ad_creation']['step'] = 4
        
        keyboard = [
            [InlineKeyboardButton("100 ভিউ - 100 পয়েন্ট", callback_data="ad_package_100")],
            [InlineKeyboardButton("500 ভিউ - 450 পয়েন্ট", callback_data="ad_package_500")],
            [InlineKeyboardButton("1000 ভিউ - 800 পয়েন্ট", callback_data="ad_package_1000")],
            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="ads")]
        ]
        
        await message.reply_text(
            "একটি বিজ্ঞাপন প্যাকেজ নির্বাচন করুন:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def select_ad_package(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if 'ad_creation' not in context.user_data:
        await query.edit_message_text("ত্রুটি: বিজ্ঞাপন তৈরি প্রক্রিয়া পুনরায় শুরু করুন।")
        return
    
    package = query.data.replace("ad_package_", "")
    if package == "100":
        views = 100
        cost = 100
    elif package == "500":
        views = 500
        cost = 450
    elif package == "1000":
        views = 1000
        cost = 800
    else:
        await query.edit_message_text("অবৈধ প্যাকেজ নির্বাচন।")
        return
    
    context.user_data['ad_creation']['total_views'] = views
    context.user_data['ad_creation']['cost'] = cost
    
    user = db.get_user(query.from_user.id)
    balance = user[7]
    
    if balance >= cost:
        # বিজ্ঞাপন তৈরি করুন
        ad_id = db.create_advertisement(
            user_id=query.from_user.id,
            title=context.user_data['ad_creation']['title'],
            description=context.user_data['ad_creation'].get('description', ''),
            target_url=context.user_data['ad_creation']['target_url'],
            total_views=views,
            cost=cost
        )
        
        # ব্যালেন্স কমানো
        db.update_balance(query.from_user.id, -cost)
        
        # লেনদেন হিসাবে যোগ করুন
        db_conn = db.conn
        cursor = db_conn.cursor()
        cursor.execute('''
        INSERT INTO transactions 
        (user_id, amount, transaction_type, status, details)
        VALUES (?, ?, ?, ?, ?)
        ''', (query.from_user.id, cost, 'ad_spend', 'completed', f'Created ad ID: {ad_id}'))
        db_conn.commit()
        
        await query.edit_message_text(
            f"✅ আপনার বিজ্ঞাপন সফলভাবে তৈরি হয়েছে!\n\n"
            f"📌 শিরোনাম: {context.user_data['ad_creation']['ti
