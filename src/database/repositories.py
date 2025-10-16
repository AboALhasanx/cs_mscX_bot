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
    
    def update_stats(self, user_id: int, questions_count: int, correct_count: int, xp_earned: int = 0):
        """
        تحديث إحصائيات المستخدم + XP
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET total_questions = total_questions + ?,
                correct_answers = correct_answers + ?,
                xp = xp + ?
            WHERE user_id = ?
        ''', (questions_count, correct_count, xp_earned, user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم تحديث إحصائيات المستخدم {user_id} (+{xp_earned} XP)")

    def add_xp(self, user_id: int, xp_amount: int) -> dict:
        """
        إضافة XP للمستخدم والتحقق من ترقية المستوى
        
        Returns:
            dict: {old_level, new_level, leveled_up, xp_gained}
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # الحصول على XP الحالي
        cursor.execute('SELECT xp FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        old_xp = result['xp'] if result else 0
        
        # إضافة XP
        new_xp = old_xp + xp_amount
        cursor.execute('UPDATE users SET xp = ? WHERE user_id = ?', (new_xp, user_id))
        conn.commit()
        conn.close()
        
        # التحقق من الترقية
        from config import get_level_from_xp
        old_level = get_level_from_xp(old_xp)['level']
        new_level = get_level_from_xp(new_xp)['level']
        
        return {
            'old_level': old_level,
            'new_level': new_level,
            'leveled_up': new_level > old_level,
            'xp_gained': xp_amount,
            'total_xp': new_xp
        }


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

class StatsRepository:
    """مستودع الإحصائيات"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_weekly_stats(self, user_id: int) -> dict:
        """
        الحصول على إحصائيات آخر 7 أيام
        
        Returns:
            dict: {total_questions, correct_answers, accuracy, active_days}
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # عدد الأسئلة والإجابات الصحيحة هذا الأسبوع
        cursor.execute('''
            SELECT 
                COUNT(*) as total_attempts,
                SUM(CASE WHEN is_correct = 1 THEN 1 ELSE 0 END) as correct,
                COUNT(DISTINCT DATE(timestamp)) as active_days
            FROM question_attempts qa
            JOIN quiz_sessions qs ON qa.session_id = qs.session_id
            WHERE qs.user_id = ? 
            AND qa.timestamp >= datetime('now', '-7 days')
        ''', (user_id,))
        
        result = cursor.fetchone()
        
        # عدد الاختبارات المكتملة هذا الأسبوع
        cursor.execute('''
            SELECT COUNT(*) as quiz_count
            FROM quiz_sessions
            WHERE user_id = ? 
            AND end_time IS NOT NULL
            AND start_time >= datetime('now', '-7 days')
        ''', (user_id,))
        
        quiz_result = cursor.fetchone()
        
        conn.close()
        
        total = result['total_attempts'] or 0
        correct = result['correct'] or 0
        accuracy = (correct / total * 100) if total > 0 else 0
        
        return {
            'total_questions': total,
            'correct_answers': correct,
            'accuracy': accuracy,
            'active_days': result['active_days'] or 0,
            'quiz_count': quiz_result['quiz_count'] or 0
        }


    def get_user_stats(self, user_id: int) -> dict:
        """الحصول على إحصائيات المستخدم الكاملة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute('''
            SELECT 
                total_questions,
                correct_answers,
                join_date
            FROM users 
            WHERE user_id = ?
        ''', (user_id,))
        
        user_row = cursor.fetchone()
        
        if not user_row:
            conn.close()
            return None
        
        # عدد الاختبارات
        cursor.execute('''
            SELECT COUNT(*) as quiz_count
            FROM quiz_sessions 
            WHERE user_id = ? AND end_time IS NOT NULL
        ''', (user_id,))
        
        quiz_count = cursor.fetchone()['quiz_count']
        
        # أفضل نتيجة
        cursor.execute('''
            SELECT 
                MAX(CAST(score AS FLOAT) / total_questions * 100) as best_score
            FROM quiz_sessions 
            WHERE user_id = ? AND end_time IS NOT NULL
        ''', (user_id,))
        
        best_score = cursor.fetchone()['best_score'] or 0
        
        # إحصائيات حسب المادة
        cursor.execute('''
            SELECT 
                subject,
                COUNT(*) as count,
                AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score
            FROM quiz_sessions 
            WHERE user_id = ? AND end_time IS NOT NULL
            GROUP BY subject
        ''', (user_id,))
        
        subject_stats = cursor.fetchall()
        
        conn.close()
        
        # حساب نسبة الدقة
        total_q = user_row['total_questions']
        correct_a = user_row['correct_answers']
        accuracy = (correct_a / total_q * 100) if total_q > 0 else 0
        
        return {
            'total_questions': total_q,
            'correct_answers': correct_a,
            'accuracy': accuracy,
            'quiz_count': quiz_count,
            'best_score': best_score,
            'join_date': user_row['join_date'],
            'subject_stats': [dict(row) for row in subject_stats]
        }
    
    def get_subject_progress(self, user_id: int) -> dict:
        """الحصول على التقدم في كل مادة"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                subject,
                chapter,
                COUNT(*) as attempts,
                AVG(CAST(score AS FLOAT) / total_questions * 100) as avg_score,
                MAX(score) as best_score,
                MAX(total_questions) as total_questions
            FROM quiz_sessions 
            WHERE user_id = ? AND end_time IS NOT NULL
            GROUP BY subject, chapter
            ORDER BY subject, chapter
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        # تنظيم البيانات حسب المادة
        progress = {}
        for row in rows:
            subject = row['subject']
            if subject not in progress:
                progress[subject] = []
            
            progress[subject].append({
                'chapter': row['chapter'],
                'attempts': row['attempts'],
                'avg_score': round(row['avg_score'], 1),
                'best_score': row['best_score'],
                'total_questions': row['total_questions']
            })
        
        return progress
