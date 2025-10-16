"""
مستودعات قاعدة البيانات (Repositories)
عمليات CRUD على قاعدة البيانات
"""

import sqlite3
from datetime import datetime
from typing import Optional, List
import logging
from src.database.models import User, QuizSession, QuestionAttempt

logger = logging.getLogger(__name__)

class UserRepository:
    """مستودع المستخدمين"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_user(self, user_id: int, username: Optional[str], first_name: str) -> User:
        """إنشاء مستخدم جديد"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, first_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, first_name))
            
            conn.commit()
            logger.info(f"✅ تم إنشاء مستخدم جديد: {user_id} - {first_name}")
            
            return User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                join_date=datetime.now(),
                total_questions=0,
                correct_answers=0
            )
        except sqlite3.IntegrityError:
            # المستخدم موجود مسبقاً
            logger.info(f"المستخدم {user_id} موجود مسبقاً")
            return self.get_user(user_id)
        finally:
            conn.close()
    
    def get_user(self, user_id: int) -> Optional[User]:
        """الحصول على بيانات مستخدم"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return User(
                user_id=row['user_id'],
                username=row['username'],
                first_name=row['first_name'],
                join_date=datetime.fromisoformat(row['join_date']),
                total_questions=row['total_questions'],
                correct_answers=row['correct_answers']
            )
        return None
    
    def update_stats(self, user_id: int, questions_count: int, correct_count: int):
        """تحديث إحصائيات المستخدم"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET total_questions = total_questions + ?,
                correct_answers = correct_answers + ?
            WHERE user_id = ?
        ''', (questions_count, correct_count, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم تحديث إحصائيات المستخدم {user_id}")

class QuizRepository:
    """مستودع الاختبارات"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_session(self, user_id: int, subject: str, chapter: str, 
                      total_questions: int) -> int:
        """إنشاء جلسة اختبار جديدة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quiz_sessions (user_id, subject, chapter, total_questions)
            VALUES (?, ?, ?, ?)
        ''', (user_id, subject, chapter, total_questions))
        
        session_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم إنشاء جلسة اختبار: {session_id}")
        return session_id
    
    def finish_session(self, session_id: int, score: int):
        """إنهاء جلسة الاختبار"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE quiz_sessions 
            SET end_time = CURRENT_TIMESTAMP, score = ?
            WHERE session_id = ?
        ''', (score, session_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم إنهاء جلسة الاختبار: {session_id}")
    
    def save_attempt(self, session_id: int, question_text: str, 
                    user_answer: int, correct_answer: int, is_correct: bool):
        """حفظ محاولة الإجابة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO question_attempts 
            (session_id, question_text, user_answer, correct_answer, is_correct)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, question_text, user_answer, correct_answer, is_correct))
        
        conn.commit()
        conn.close()
    
    def get_user_sessions(self, user_id: int, limit: int = 10) -> List[QuizSession]:
        """الحصول على آخر جلسات المستخدم"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quiz_sessions 
            WHERE user_id = ? 
            ORDER BY start_time DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        sessions = []
        for row in rows:
            sessions.append(QuizSession(
                session_id=row['session_id'],
                user_id=row['user_id'],
                subject=row['subject'],
                chapter=row['chapter'],
                start_time=datetime.fromisoformat(row['start_time']),
                end_time=datetime.fromisoformat(row['end_time']) if row['end_time'] else None,
                score=row['score'],
                total_questions=row['total_questions']
            ))
        
        return sessions
