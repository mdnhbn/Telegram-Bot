import sqlite3
from config import Config
import random
import string

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(Config.DB_NAME)
        self.create_tables()
        self.initialize_settings()

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
        
        # ডিপোজিট টেবিল (আপডেটেড)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deposits (
            deposit_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT NOT NULL,  # bkash, usdt, ton, doge
            payment_details TEXT,  # trxid, wallet address etc.
            status TEXT DEFAULT 'pending',
            request_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completion_time TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        
        # সেটিংস টেবিল (নতুন)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        ''')
        
        self.conn.commit()

    def initialize_settings(self):
        cursor = self.conn.cursor()
        
        # ডিফল্ট সেটিংস যোগ করুন যদি না থাকে
        default_settings = {
            'BKASH_MERCHANT_NO': Config.BKASH_MERCHANT_NO,
            'USDT_TRC20_WALLET': Config.USDT_TRC20_WALLET,
            'TON_WALLET': Config.TON_WALLET,
            'DOGE_WALLET': Config.DOGE_WALLET,
            'BKASH_ENABLED': '1' if Config.BKASH_ENABLED else '0',
            'CRYPTO_ENABLED': '1' if Config.CRYPTO_ENABLED else '0'
        }
        
        for key, value in default_settings.items():
            cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value)
            VALUES (?, ?)
            ''', (key, value))
        
        self.conn.commit()

    # সেটিংস সম্পর্কিত মেথড (নতুন)
    def get_setting(self, key):
        cursor = self.conn.cursor()
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        result = cursor.fetchone()
        return result[0] if result else None

    def update_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
        ''', (key, str(value)))
        self.conn.commit()

    def get_all_settings(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT key, value FROM settings')
        return {row[0]: row[1] for row in cursor.fetchall()}

    # ডিপোজিট সম্পর্কিত মেথড (আপডেটেড)
    def create_deposit_request(self, deposit_id, user_id, amount, payment_method, payment_details=None):
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO deposits (deposit_id, user_id, amount, payment_method, payment_details, status)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (deposit_id, user_id, amount, payment_method, payment_details, 'pending'))
        self.conn.commit()

    def update_deposit_status(self, deposit_id, status, payment_details=None):
        cursor = self.conn.cursor()
        
        if payment_details:
            cursor.execute('''
            UPDATE deposits 
            SET status = ?, payment_details = ?, completion_time = CURRENT_TIMESTAMP
            WHERE deposit_id = ?
            ''', (status, payment_details, deposit_id))
        else:
            cursor.execute('''
            UPDATE deposits 
            SET status = ?, completion_time = CURRENT_TIMESTAMP
            WHERE deposit_id = ?
            ''', (status, deposit_id))
        
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
        cursor.execute('SELECT * FROM deposits WHERE status = ? ORDER BY request_time DESC', ('pending',))
        return cursor.fetchall()

    # অন্যান্য মেথড (পূর্বের মতোই)
    # ... [পূর্বের সমস্ত মেথড একই থাকবে, শুধু আপডেটেড মেথডগুলো দেখানো হয়েছে]
