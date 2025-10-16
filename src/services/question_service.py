import json
import random
from pathlib import Path

class QuestionService:
    """خدمة إدارة الأسئلة"""
    
    def __init__(self, questions_dir: str):
        self.questions_dir = Path(questions_dir)
    
    def load_questions(self, filename: str) -> list:
        """
        تحميل الأسئلة من ملف JSON
        
        Args:
            filename: اسم ملف JSON (مثل 'test_quiz.json')
        
        Returns:
            قائمة بالأسئلة
        """
        filepath = self.questions_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"الملف غير موجود: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            questions = json.load(f)
        
        return questions
    
    def get_random_questions(self, questions: list, count: int) -> list:
        """
        اختيار أسئلة عشوائية
        
        Args:
            questions: قائمة الأسئلة الكاملة
            count: عدد الأسئلة المطلوبة
        
        Returns:
            قائمة بالأسئلة العشوائية
        """
        return random.sample(questions, min(len(questions), count))
    
    def shuffle_options(self, question: dict) -> dict:
        """
        خلط خيارات السؤال (اختياري - للمستقبل)
        """
        # هذه الوظيفة للتوسع المستقبلي
        # حالياً Telegram Quiz يخلط الخيارات تلقائياً
        return question
