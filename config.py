import os
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv('BOT_TOKEN')

# إعدادات الاختبار
QUESTIONS_PER_QUIZ = 5
PASSING_SCORE = 3  # 60%

# مسارات الملفات
QUESTIONS_DIR = "data/questions"
DATABASE_PATH = "data/database/quiz_bot.db"

# رسائل
WELCOME_MESSAGE = """
🎓 مرحباً بك في بوت اختبارات التنافسي!

اضغط /start_quiz لبدء اختبار تجريبي (5 أسئلة)
اضغط /help لعرض الأوامر المتاحة
"""

HELP_MESSAGE = """
📚 **الأوامر المتاحة:**

/start - بداية التفاعل مع البوت
/start_quiz - بدء اختبار تجريبي
/help - عرض هذه الرسالة
"""

QUIZ_START_MESSAGE = """
🚀 بدأ الاختبار!

عدد الأسئلة: {total}
اضغط على الإجابة الصحيحة في كل سؤال.

جاهز؟ السؤال الأول قادم...
"""

QUIZ_FINISHED_MESSAGE = """
✅ انتهى الاختبار!

📊 النتيجة: {score}/{total}
📈 النسبة: {percentage}%

{result_emoji} {result_text}

اكتب /start_quiz لإعادة المحاولة!
"""
