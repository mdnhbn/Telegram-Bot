import sqlite3
from config import Config

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # ব্যবহারকারী টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            wallet_address TEXT,
            wallet_type TEXT,
            balance REAL DEFAULT 0,
            total_earned REAL DEFAULT 0,
            referral_count INTEGER DEFAULT 0,
            referral_earnings REAL DEFAULT 0,
            is_verified BOOLEAN DEFAULT FALSE,
            is_banned BOOLEAN DEFAULT FALSE
        )
        ''')
        
        # টাস্ক টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            url TEXT NOT NULL,
            reward REAL NOT NULL,
            is_active BOOLEAN DEFAULT TRUE
        )
        ''')
        
        # ব্যবহারকারী টাস্ক টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_tasks (
            user_task_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            task_id INTEGER NOT NULL,
            completion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (task_id) REFERENCES tasks(task_id)
        )
        ''')
        
        # বিজ্ঞাপন টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS advertisements (
            ad_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            target_url TEXT NOT NULL,
            total_views INTEGER NOT NULL,
            completed_views INTEGER DEFAULT 0,
            cost REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # রেফারেল টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            referral_id INTEGER PRIMARY KEY AUTOINCREMENT,
            referrer_id INTEGER NOT NULL,
            referred_id INTEGER NOT NULL,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (referrer_id) REFERENCES users(user_id),
            FOREIGN KEY (referred_id) REFERENCES users(user_id)
        )
        ''')
        
        # লেনদেন টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            transaction_type TEXT NOT NULL,  # deposit, withdraw, task, referral, ad_spend
            status TEXT DEFAULT 'pending',
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # ডিপোজিট টেবিল
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            deposit_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            wallet_type TEXT NOT NULL,
            tx_hash TEXT,
            status TEXT DEFAULT 'pending',
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        self.conn.commit()

    # ব্যবহারকারী সম্পর্কিত মেথড
    def add_user(self, user_id, username, first_name, last_name):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name)
        VALUES (?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name))
        self.conn.commit()
        return cursor.lastrowid

    def get_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def update_user_wallet(self, user_id, wallet_address, wallet_type):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE users 
        SET wallet_address = ?, wallet_type = ?
        WHERE user_id = ?
        ''', (wallet_address, wallet_type, user_id))
        self.conn.commit()

    def verify_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_verified = TRUE WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
        if amount > 0:
            cursor.execute('UPDATE users SET total_earned = total_earned + ? WHERE user_id = ?', (amount, user_id))
        self.conn.commit()

    # টাস্ক সম্পর্কিত মেথড
    def add_task(self, title, description, url, reward):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO tasks (title, description, url, reward)
        VALUES (?, ?, ?, ?)
        ''', (title, description, url, reward))
        self.conn.commit()
        return cursor.lastrowid

    def get_active_tasks(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE is_active = TRUE')
        return cursor.fetchall()

    def get_task(self, task_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM tasks WHERE task_id = ?', (task_id,))
        return cursor.fetchone()

    def complete_task(self, user_id, task_id):
        cursor = self.conn.cursor()
        reward = self.get_task(task_id)[4]
        
        # টাস্ক সম্পন্ন করুন
        cursor.execute('''
        INSERT INTO user_tasks (user_id, task_id)
        VALUES (?, ?)
        ''', (user_id, task_id))
        
        # ব্যালেন্স আপডেট করুন
        self.update_balance(user_id, reward)
        
        # লেনদেন হিসাবে যোগ করুন
        cursor.execute('''
        INSERT INTO transactions (user_id, amount, transaction_type, status, details)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, reward, 'task', 'completed', f'Completed task ID: {task_id}'))
        
        self.conn.commit()
        return reward

    def get_user_last_task_time(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT completion_time FROM user_tasks 
        WHERE user_id = ? 
        ORDER BY completion_time DESC 
        LIMIT 1
        ''', (user_id,))
        result = cursor.fetchone()
        return result[0] if result else None

    # বিজ্ঞাপন সম্পর্কিত মেথড
    def create_advertisement(self, user_id, title, description, target_url, total_views, cost):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO advertisements 
        (user_id, title, description, target_url, total_views, cost)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, title, description, target_url, total_views, cost))
        self.conn.commit()
        return cursor.lastrowid

    def get_user_ads(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM advertisements WHERE user_id = ? ORDER BY creation_date DESC', (user_id,))
        return cursor.fetchall()

    def update_ad_views(self, ad_id, views_to_add=1):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE advertisements 
        SET completed_views = completed_views + ?
        WHERE ad_id = ? AND completed_views < total_views
        ''', (views_to_add, ad_id))
        self.conn.commit()
        
        # বিজ্ঞাপনের অবস্থা চেক করুন
        cursor.execute('''
        UPDATE advertisements
        SET status = 'completed'
        WHERE ad_id = ? AND completed_views >= total_views
        ''', (ad_id,))
        self.conn.commit()

    # রেফারেল সম্পর্কিত মেথড
    def add_referral(self, referrer_id, referred_id):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO referrals (referrer_id, referred_id)
        VALUES (?, ?)
        ''', (referrer_id, referred_id))
        
        # রেফারেল কাউন্ট আপডেট করুন
        cursor.execute('''
        UPDATE users 
        SET referral_count = referral_count + 1 
        WHERE user_id = ?
        ''', (referrer_id,))
        
        self.conn.commit()
        return cursor.lastrowid

    # লেনদেন সম্পর্কিত মেথড
    def create_withdrawal(self, user_id, amount, wallet_address):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO transactions 
        (user_id, amount, transaction_type, status, details)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, 'withdraw', 'pending', f'Withdrawal to: {wallet_address}'))
        
        # ব্যালেন্স কমানো
        self.update_balance(user_id, -amount)
        
        self.conn.commit()
        return cursor.lastrowid

    def create_deposit_request(self, deposit_id, user_id, amount, wallet_type):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO deposits 
        (deposit_id, user_id, amount, wallet_type)
        VALUES (?, ?, ?, ?)
        ''', (deposit_id, user_id, amount, wallet_type))
        self.conn.commit()

    def update_deposit_status(self, deposit_id, tx_hash, status):
        cursor = self.conn.cursor()
        cursor.execute('''
        UPDATE deposits 
        SET tx_hash = ?, status = ?, completion_time = CURRENT_TIMESTAMP
        WHERE deposit_id = ?
        ''', (tx_hash, status, deposit_id))
        
        if status == 'completed':
            deposit = self.get_deposit(deposit_id)
            if deposit:
                user_id = deposit[1]
                amount = deposit[2]
                
                # ব্যালেন্স আপডেট করুন
                self.update_balance(user_id, amount)
                
                # লেনদেন হিসাবে যোগ করুন
                cursor.execute('''
                INSERT INTO transactions 
                (user_id, amount, transaction_type, status, details)
                VALUES (?, ?, ?, ?, ?)
                ''', (user_id, amount, 'deposit', 'completed', f'Deposit ID: {deposit_id}'))
        
        self.conn.commit()

    def get_deposit(self, deposit_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM deposits WHERE deposit_id = ?', (deposit_id,))
        return cursor.fetchone()

    def get_pending_deposits(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM deposits WHERE status = ?', ('pending',))
        return cursor.fetchall()

    # অ্যাডমিন মেথড
    def get_all_users(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY join_date DESC')
        return cursor.fetchall()

    def ban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = TRUE WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def unban_user(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_banned = FALSE WHERE user_id = ?', (user_id,))
        self.conn.commit()

    def admin_update_balance(self, user_id, amount):
        cursor = self.conn.cursor()
        self.update_balance(user_id, amount)
        
        # লেনদেন হিসাবে যোগ করুন
        cursor.execute('''
        INSERT INTO transactions 
        (user_id, amount, transaction_type, status, details)
        VALUES (?, ?, ?, ?, ?)
        ''', (user_id, amount, 'admin_adjustment', 'completed', 'Balance adjusted by admin'))
        
        self.conn.commit()

    def get_user_transactions(self, user_id, limit=10):
        cursor = self.conn.cursor()
        cursor.execute('''
        SELECT * FROM transactions 
        WHERE user_id = ? 
        ORDER BY timestamp DESC 
        LIMIT ?
        ''', (user_id, limit))
        return cursor.fetchall()
