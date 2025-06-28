from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from config import Config
from database import Database
import random
import string

db = Database()

# হেল্পার ফাংশন
def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

async def admin_menu(update: Update, context: CallbackContext):
    user = update.effective_user
    if user.id not in Config.ADMIN_IDS:
        await update.message.reply_text("আপনি অ্যাডমিন নন।")
        return
    
    keyboard = [
        [InlineKeyboardButton("👥 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")],
        [InlineKeyboardButton("📝 টাস্ক ব্যবস্থাপনা", callback_data="admin_task_management")],
        [InlineKeyboardButton("📢 বিজ্ঞাপন ব্যবস্থাপনা", callback_data="admin_ad_management")],
        [InlineKeyboardButton("💰 আর্থিক ব্যবস্থাপনা", callback_data="admin_financial_management")],
        [InlineKeyboardButton("⚙️ সেটিংস", callback_data="admin_settings")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট", callback_data="admin_broadcast")]
    ]
    
    await update.message.reply_text(
        "অ্যাডমিন প্যানেল:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_user_management(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("🔍 ব্যবহারকারী খুঁজুন", callback_data="admin_find_user")],
        [InlineKeyboardButton("🚫 ব্যবহারকারী ব্যান করুন", callback_data="admin_ban_user")],
        [InlineKeyboardButton("✅ ব্যবহারকারী আনবান করুন", callback_data="admin_unban_user")],
        [InlineKeyboardButton("➕ ব্যালেন্স যোগ করুন", callback_data="admin_add_balance")],
        [InlineKeyboardButton("➖ ব্যালেন্স কমান", callback_data="admin_deduct_balance")],
        [InlineKeyboardButton("🔙 অ্যাডমিন মেনু", callback_data="admin_menu")]
    ]
    
    await query.edit_message_text(
        "ব্যবহারকারী ব্যবস্থাপনা:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_find_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "ব্যবহারকারীর ইউজারনেম বা আইডি লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
        ])
    )
    context.user_data['admin_action'] = 'find_user'

async def admin_process_find_user(update: Update, context: CallbackContext):
    message = update.message
    search_term = message.text.strip()
    
    try:
        # ইউজারনেম বা আইডি দ্বারা খুঁজুন
        if search_term.startswith('@'):
            search_term = search_term[1:]
            user = db.conn.execute('SELECT * FROM users WHERE username = ?', (search_term,)).fetchone()
        else:
            user_id = int(search_term)
            user = db.get_user(user_id)
        
        if user:
            text = (
                f"👤 ব্যবহারকারী তথ্য:\n\n"
                f"🆔 আইডি: {user[0]}\n"
                f"👤 নাম: {user[2]} {user[3] or ''}\n"
                f"📛 ইউজারনেম: @{user[1] or 'N/A'}\n"
                f"📅 যোগদান তারিখ: {user[4]}\n"
                f"💰 ব্যালেন্স: {user[7]:.2f} পয়েন্ট\n"
                f"💵 মোট আয়: {user[8]:.2f} পয়েন্ট\n"
                f"👥 রেফারেল: {user[9]} জন\n"
                f"🔒 অবস্থা: {'ব্যান' if user[12] else 'সক্রিয়'}\n"
                f"✅ ভেরিফাইড: {'হ্যাঁ' if user[11] else 'না'}"
            )
            
            keyboard = [
                [InlineKeyboardButton("➕ ব্যালেন্স যোগ", callback_data=f"admin_add_bal_{user[0]}")],
                [InlineKeyboardButton("➖ ব্যালেন্স কমান", callback_data=f"admin_deduct_bal_{user[0]}")],
                [InlineKeyboardButton("🚫 ব্যান করুন", callback_data=f"admin_ban_{user[0]}")] if not user[12] else 
                [InlineKeyboardButton("✅ আনবান করুন", callback_data=f"admin_unban_{user[0]}")],
                [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
            ]
            
            await message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard)
        else:
            await message.reply_text("ব্যবহারকারী পাওয়া যায়নি।")
    except ValueError:
        await message.reply_text("অবৈধ ইনপুট। দয়া করে একটি বৈধ ইউজারনেম বা আইডি লিখুন।")

async def admin_ban_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('admin_ban_'):
        user_id = int(query.data.replace('admin_ban_', ''))
        db.ban_user(user_id)
        await query.edit_message_text(f"ব্যবহারকারী {user_id} কে ব্যান করা হয়েছে।")
        return
    
    await query.edit_message_text(
        "ব্যবহারকারীর ইউজারনেম বা আইডি লিখুন যাকে ব্যান করতে চান:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
        ])
    )
    context.user_data['admin_action'] = 'ban_user'

async def admin_unban_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('admin_unban_'):
        user_id = int(query.data.replace('admin_unban_', ''))
        db.unban_user(user_id)
        await query.edit_message_text(f"ব্যবহারকারী {user_id} কে আনবান করা হয়েছে।")
        return
    
    await query.edit_message_text(
        "ব্যবহারকারীর ইউজারনেম বা আইডি লিখুন যাকে আনবান করতে চান:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
        ])
    )
    context.user_data['admin_action'] = 'unban_user'

async def admin_add_balance(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('admin_add_bal_'):
        user_id = int(query.data.replace('admin_add_bal_', ''))
        context.user_data['admin_user_id'] = user_id
        context.user_data['admin_action'] = 'add_balance'
        
        await query.edit_message_text(
            f"ব্যবহারকারী {user_id}-এর অ্যাকাউন্টে যোগ করতে চান এমন পয়েন্টের পরিমাণ লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
            ])
        )
        return
    
    await query.edit_message_text(
        "ব্যবহারকারীর ইউজারনেম বা আইডি লিখুন যার অ্যাকাউন্টে পয়েন্ট যোগ করতে চান:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
        ])
    )
    context.user_data['admin_action'] = 'add_balance_user'

async def admin_deduct_balance(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    if query.data.startswith('admin_deduct_bal_'):
        user_id = int(query.data.replace('admin_deduct_bal_', ''))
        context.user_data['admin_user_id'] = user_id
        context.user_data['admin_action'] = 'deduct_balance'
        
        await query.edit_message_text(
            f"ব্যবহারকারী {user_id}-এর অ্যাকাউন্ট থেকে কমানোর জন্য পয়েন্টের পরিমাণ লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
            ])
        )
        return
    
    await query.edit_message_text(
        "ব্যবহারকারীর ইউজারনেম বা আইডি লিখুন যার অ্যাকাউন্ট থেকে পয়েন্ট কমানো হবে:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 ব্যবহারকারী ব্যবস্থাপনা", callback_data="admin_user_management")]
        ])
    )
    context.user_data['admin_action'] = 'deduct_balance_user'

async def admin_process_balance_action(update: Update, context: CallbackContext):
    message = update.message
    admin_action = context.user_data.get('admin_action')
    
    if admin_action in ('add_balance_user', 'deduct_balance_user'):
        search_term = message.text.strip()
        try:
            if search_term.startswith('@'):
                search_term = search_term[1:]
                user = db.conn.execute('SELECT * FROM users WHERE username = ?', (search_term,)).fetchone()
            else:
                user_id = int(search_term)
                user = db.get_user(user_id)
            
            if user:
                context.user_data['admin_user_id'] = user[0]
                if admin_action == 'add_balance_user':
                    context.user_data['admin_action'] = 'add_balance'
                    await message.reply_text(
                        f"ব্যবহারকারী {user[0]}-এর অ্যাকাউন্টে যোগ করতে চান এমন পয়েন্টের পরিমাণ লিখুন:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_user_management")]
                        ])
                    )
                else:
                    context.user_data['admin_action'] = 'deduct_balance'
                    await message.reply_text(
                        f"ব্যবহারকারী {user[0]}-এর অ্যাকাউন্ট থেকে কমানোর জন্য পয়েন্টের পরিমাণ লিখুন:",
                        reply_markup=InlineKeyboardMarkup([
                            [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_user_management")]
                        ])
                    )
            else:
                await message.reply_text("ব্যবহারকারী পাওয়া যায়নি।")
        except ValueError:
            await message.reply_text("অবৈধ ইনপুট। দয়া করে একটি বৈধ ইউজারনেম বা আইডি লিখুন।")
    
    elif admin_action in ('add_balance', 'deduct_balance'):
        try:
            amount = float(message.text)
            user_id = context.user_data['admin_user_id']
            
            if admin_action == 'add_balance':
                db.admin_update_balance(user_id, amount)
                await message.reply_text(
                    f"✅ {amount:.2f} পয়েন্ট ব্যবহারকারী {user_id}-এর অ্যাকাউন্টে যোগ করা হয়েছে।"
                )
            else:
                user = db.get_user(user_id)
                if user[7] >= amount:
                    db.admin_update_balance(user_id, -amount)
                    await message.reply_text(
                        f"✅ {amount:.2f} পয়েন্ট ব্যবহারকারী {user_id}-এর অ্যাকাউন্ট থেকে কমানো হয়েছে।"
                    )
                else:
                    await message.reply_text(
                        f"ত্রুটি: ব্যবহারকারীর ব্যালেন্স {user[7]:.2f} পয়েন্ট, যা অনুরোধকৃত {amount:.2f} পয়েন্টের চেয়ে কম।"
                    )
            
            del context.user_data['admin_action']
            del context.user_data['admin_user_id']
        except ValueError:
            await message.reply_text("দুঃখিত, দয়া করে একটি বৈধ সংখ্যা লিখুন।")

async def admin_task_management(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("➕ নতুন টাস্ক যোগ করুন", callback_data="admin_add_task")],
        [InlineKeyboardButton("📝 টাস্ক তালিকা", callback_data="admin_list_tasks")],
        [InlineKeyboardButton("🚫 টাস্ক ডিলিট করুন", callback_data="admin_delete_task")],
        [InlineKeyboardButton("🔙 অ্যাডমিন মেনু", callback_data="admin_menu")]
    ]
    
    await query.edit_message_text(
        "টাস্ক ব্যবস্থাপনা:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_add_task(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "নতুন টাস্কের শিরোনাম লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 টাস্ক ব্যবস্থাপনা", callback_data="admin_task_management")]
        ])
    )
    context.user_data['admin_task'] = {'step': 1}

async def admin_process_add_task(update: Update, context: CallbackContext):
    message = update.message
    step = context.user_data['admin_task']['step']
    text = message.text
    
    if step == 1:
        context.user_data['admin_task']['title'] = text
        context.user_data['admin_task']['step'] = 2
        
        await message.reply_text(
            "টাস্কের বিবরণ লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_task_management")]
            ])
        )
    elif step == 2:
        context.user_data['admin_task']['description'] = text
        context.user_data['admin_task']['step'] = 3
        
        await message.reply_text(
            "টাস্কের URL লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_task_management")]
            ])
        )
    elif step == 3:
        if not text.startswith(('http://', 'https://')):
            await message.reply_text("দয়া করে একটি বৈধ URL লিখুন (http:// বা https:// দিয়ে শুরু করতে হবে)।")
            return
        
        context.user_data['admin_task']['url'] = text
        context.user_data['admin_task']['step'] = 4
        
        await message.reply_text(
            "টাস্কের পুরস্কার (পয়েন্ট) লিখুন:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বাতিল করুন", callback_data="admin_task_management")]
            ])
        )
    elif step == 4:
        try:
            reward = float(text)
            title = context.user_data['admin_task']['title']
            description = context.user_data['admin_task'].get('description', '')
            url = context.user_data['admin_task']['url']
            
            task_id = db.add_task(title, description, url, reward)
            
            await message.reply_text(
                f"✅ নতুন টাস্ক যোগ করা হয়েছে!\n\n"
                f"🆔 আইডি: {task_id}\n"
                f"📌 শিরোনাম: {title}\n"
                f"💰 পুরস্কার: {reward:.2f} পয়েন্ট"
            )
            
            del context.user_data['admin_task']
        except ValueError:
            await message.reply_text("দুঃখিত, দয়া করে একটি বৈধ সংখ্যা লিখুন।")

async def admin_list_tasks(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    tasks = db.get_active_tasks()
    if not tasks:
        await query.edit_message_text(
            "কোন সক্রিয় টাস্ক পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ নতুন টাস্ক যোগ করুন", callback_data="admin_add_task")],
                [InlineKeyboardButton("🔙 টাস্ক ব্যবস্থাপনা", callback_data="admin_task_management")]
            ])
        )
        return
    
    text = "📝 সক্রিয় টাস্কের তালিকা:\n\n"
    for task in tasks:
        text += f"🆔 {task[0]}\n📌 {task[1]}\n💰 {task[4]:.2f} পয়েন্ট\n\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ নতুন টাস্ক যোগ করুন", callback_data="admin_add_task")],
        [InlineKeyboardButton("🚫 টাস্ক ডিলিট করুন", callback_data="admin_delete_task")],
        [InlineKeyboardButton("🔙 টাস্ক ব্যবস্থাপনা", callback_data="admin_task_management")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_delete_task(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "ডিলিট করতে চাওয়া টাস্কের আইডি লিখুন:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 টাস্ক ব্যবস্থাপনা", callback_data="admin_task_management")]
        ])
    )
    context.user_data['admin_action'] = 'delete_task'

async def admin_process_delete_task(update: Update, context: CallbackContext):
    message = update.message
    try:
        task_id = int(message.text)
        task = db.get_task(task_id)
        
        if task:
            db.conn.execute('UPDATE tasks SET is_active = FALSE WHERE task_id = ?', (task_id,))
            db.conn.commit()
            await message.reply_text(f"টাস্ক {task_id} সফলভাবে ডিলিট করা হয়েছে।")
        else:
            await message.reply_text("টাস্ক পাওয়া যায়নি।")
    except ValueError:
        await message.reply_text("দুঃখিত, দয়া করে একটি বৈধ টাস্ক আইডি লিখুন।")

async def admin_ad_management(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    pending_deposits = db.get_pending_deposits()
    pending_count = len(pending_deposits) if pending_deposits else 0
    
    keyboard = [
        [InlineKeyboardButton("📊 বিজ্ঞাপন তালিকা", callback_data="admin_list_ads")],
        [InlineKeyboardButton("✅ ডিপোজিট অনুমোদন করুন", callback_data="admin_approve_deposits")],
        [InlineKeyboardButton(f"⏳ পেন্ডিং ডিপোজিট ({pending_count})", callback_data="admin_pending_deposits")],
        [InlineKeyboardButton("🔙 অ্যাডমিন মেনু", callback_data="admin_menu")]
    ]
    
    await query.edit_message_text(
        "বিজ্ঞাপন ব্যবস্থাপনা:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_list_ads(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    ads = db.conn.execute('''
    SELECT a.*, u.username 
    FROM advertisements a
    LEFT JOIN users u ON a.user_id = u.user_id
    ORDER BY a.creation_date DESC
    LIMIT 50
    ''').fetchall()
    
    if not ads:
        await query.edit_message_text(
            "কোন বিজ্ঞাপন পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বিজ্ঞাপন ব্যবস্থাপনা", callback_data="admin_ad_management")]
            ])
        )
        return
    
    text = "📊 বিজ্ঞাপন তালিকা:\n\n"
    for ad in ads:
        status = "✅ সম্পূর্ণ" if ad[7] == 'completed' else "🚀 চলমান" if ad[7] == 'active' else "⏳ পেন্ডিং"
        text += (
            f"🆔 {ad[0]}\n"
            f"👤 @{ad[9] or 'N/A'} ({ad[1]})\n"
            f"📌 {ad[2]}\n"
            f"👁️‍🗨️ {ad[6]}/{ad[5]} ভিউ\n"
            f"💵 {ad[8]:.2f} পয়েন্ট\n"
            f"🔄 {status}\n\n"
        )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 বিজ্ঞাপন ব্যবস্থাপনা", callback_data="admin_ad_management")]
        ])
    )

async def admin_pending_deposits(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    
    deposits = db.get_pending_deposits()
    if not deposits:
        await query.edit_message_text(
            "কোন পেন্ডিং ডিপোজিট পাওয়া যায়নি।",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 বিজ্ঞাপন ব্যবস্থাপনা", callback_data="admin_ad_management")]
            ])
        )
        return
    
    text = "⏳ পেন্ডিং ডিপোজিট:\n\n"
    for deposit in deposits:
        user = db.get_user(deposit[1])
        username = f"@{user[1]}" if user and user[1] else f"User {deposit[1]}"
        text += (
            f"🆔 {deposit[0]}\n"
            f"👤 {username}\n"
            f"💰 {deposit[2]:.2f} পয়েন্ট\n"
            f"💳 {deposit[3]}\n"
            f"📅 {deposit[5]}\n\n"
        )
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ অনুমোদন করুন", callback_data="admin_approve_deposits")],
            [InlineKeyboardButton("🔙 বিজ্ঞাপন ব্যবস্থাপনা", callback_data="admin_ad_management")]
        ])
    )

async def admin_approve_deposits(update: Update, context: CallbackContext):
    query = update.callback_query
    a
