"""
مدير قاعدة البيانات (Database Manager)
إنشاء وإدارة الاتصال بقاعدة بيانات SQLite
"""

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير قاعدة البيانات"""
    
    def __init__(self, db_path: str):
        """
        تهيئة مدير قاعدة البيانات
        
        Args:
            db_path: مسار ملف قاعدة البيانات
        """
        self.db_path = Path(db_path)
        
        # إنشاء مجلد database إذا لم يكن موجود
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # إنشاء الجداول
        self._create_tables()
        
        logger.info(f"✅ قاعدة البيانات جاهزة: {self.db_path}")
    
    def get_connection(self) -> sqlite3.Connection:
        """إنشاء اتصال جديد بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # للحصول على النتائج كـ dict
        return conn
    
    def _create_tables(self):
        """إنشاء جداول قاعدة البيانات إذا لم تكن موجودة"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # جدول المستخدمين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT NOT NULL,
                join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_questions INTEGER DEFAULT 0,
                correct_answers INTEGER DEFAULT 0,
                xp INTEGER DEFAULT 0
            )
        ''')
        
        # إضافة عمود XP للمستخدمين القدامى (إذا لم يكن موجود)
        try:
            cursor.execute('ALTER TABLE users ADD COLUMN xp INTEGER DEFAULT 0')
            logger.info("✅ تم إضافة عمود XP لجدول users")
        except sqlite3.OperationalError:
            # العمود موجود مسبقاً
            pass
        
        # جدول جلسات الاختبارات
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                subject TEXT NOT NULL,
                chapter TEXT NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                score INTEGER DEFAULT 0,
                total_questions INTEGER NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        
        # جدول محاولات الأسئلة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS question_attempts (
                attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                user_answer INTEGER NOT NULL,
                correct_answer INTEGER NOT NULL,
                is_correct BOOLEAN NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES quiz_sessions (session_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("✅ تم إنشاء جداول قاعدة البيانات بنجاح")
