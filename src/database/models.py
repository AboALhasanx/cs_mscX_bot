"""
نماذج البيانات (Data Models)
تعريف شكل البيانات في قاعدة البيانات
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class User:
    """نموذج المستخدم"""
    user_id: int
    username: Optional[str]
    first_name: str
    join_date: datetime
    total_questions: int = 0
    correct_answers: int = 0
    
    @property
    def accuracy(self) -> float:
        """حساب نسبة الدقة"""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_answers / self.total_questions) * 100

@dataclass
class QuizSession:
    """نموذج جلسة الاختبار"""
    session_id: Optional[int]
    user_id: int
    subject: str
    chapter: str
    start_time: datetime
    end_time: Optional[datetime]
    score: int
    total_questions: int
    
    @property
    def percentage(self) -> float:
        """حساب النسبة المئوية"""
        if self.total_questions == 0:
            return 0.0
        return (self.score / self.total_questions) * 100
    
    @property
    def duration_minutes(self) -> int:
        """حساب المدة بالدقائق"""
        if not self.end_time:
            return 0
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

@dataclass
class QuestionAttempt:
    """نموذج محاولة الإجابة على سؤال"""
    attempt_id: Optional[int]
    session_id: int
    question_text: str
    user_answer: int
    correct_answer: int
    is_correct: bool
    timestamp: datetime
