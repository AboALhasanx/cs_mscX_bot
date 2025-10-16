import os
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

# إعدادات البوت
BOT_TOKEN = os.getenv('BOT_TOKEN')

# إعدادات الاختبار
USE_ALL_QUESTIONS = True  # استخدام جميع أسئلة الفصل
QUESTIONS_PER_QUIZ = 5  # يُستخدم فقط إذا كان USE_ALL_QUESTIONS = False
PASSING_SCORE = 3  # 60%

# مسارات الملفات
QUESTIONS_DIR = "data/questions"
DATABASE_PATH = "data/database/quiz_bot.db"

# إعدادات تحميل الأسئلة من GitHub
GITHUB_RAW_URL = "https://raw.githubusercontent.com/AboALhasanx/json-files/refs/heads/main"

# تفعيل/تعطيل التحميل من الإنترنت
USE_ONLINE_QUESTIONS = True  # True = تحميل من GitHub, False = تحميل من الملفات المحلية

# Cache للأسئلة (لتجنب التحميل المتكرر)
CACHE_QUESTIONS = True
CACHE_DURATION_MINUTES = 60  # مدة صلاحية الـ Cache

# مطابقة أسماء المواد مع مجلدات GitHub
SUBJECT_TO_FOLDER = {
    'ai': 'ai_quizzes',
    'networks': 'networks_quizzes',
    'oop': 'oop_quizzes',
    'se': 'se_quizzes',
    'ds_algo': 'ds_algo_quizzes',
    'os': 'os_quizzes'
}

# رسائل
WELCOME_MESSAGE = """
🎓 مرحباً بك في بوت اختبارات التنافسي!

اضغط /start لبدء رحلتك التعليمية
اضغط /help لعرض الأوامر المتاحة
"""

HELP_MESSAGE = """
📚 **الأوامر المتاحة:**

/start - بداية التفاعل مع البوت
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

اكتب /start للعودة للقائمة الرئيسية
"""

# رسائل حسب النتيجة
def get_result_message(percentage: float) -> tuple:
    """
    الحصول على رسالة مخصصة حسب النسبة
    
    Returns:
        (emoji, text)
    """
    if percentage >= 90:
        return ("🏆", "ممتاز جداً! أداء استثنائي")
    elif percentage >= 80:
        return ("🎉", "ممتاز! نتيجة رائعة")
    elif percentage >= 70:
        return ("👍", "جيد جداً! استمر بالتقدم")
    elif percentage >= 60:
        return ("📚", "جيد - يمكنك تحسين نتيجتك")
    elif percentage >= 50:
        return ("💪", "مقبول - راجع المادة جيداً")
    else:
        return ("📖", "حاول مرة أخرى - ركز على المواضيع الضعيفة")

# ===============================
# نظام الرسائل التحفيزية
# ===============================

MOTIVATIONAL_MESSAGES = [
    "استمر بالتقدم! 💪",
    "أنت على الطريق الصحيح! 🎯",
    "كل سؤال خطوة نحو النجاح! 🚀",
    "التدريب يصنع الكمال! 📚",
    "لا تستسلم أبداً! 🔥",
    "ممتاز! استمر هكذا! ⭐",
    "كل يوم تتحسن أكثر! 🌟",
    "الإصرار هو مفتاح النجاح! 🔑",
    "أنت أقرب للهدف! 🎯",
    "الجهد المستمر يؤتي ثماره! 🌱"
]

def get_random_motivational_message() -> str:
    """اختيار رسالة تحفيزية عشوائية"""
    import random
    return random.choice(MOTIVATIONAL_MESSAGES)

# ===============================
# نظام المستويات والنقاط - 100 مستوى
# ===============================

# نقاط XP لكل إجابة
XP_PER_CORRECT_ANSWER = 10      # سؤال صحيح = 10 XP
XP_PER_WRONG_ANSWER = 2          # سؤال خطأ = 2 XP
XP_BONUS_PERFECT_QUIZ = 25       # إذا 100% = 25 XP إضافية
XP_BONUS_STREAK = 5              # كل يوم متواصل = 5 XP

# صيغة حساب XP المطلوب لكل مستوى
def calculate_xp_for_level(level: int) -> int:
    """
    حساب XP المطلوب للوصول لمستوى معين
    
    الصيغة: XP = 100 * level * (level + 1) / 2
    
    Examples:
        Level 1: 100 XP
        Level 2: 300 XP (يحتاج 200 إضافية)
        Level 5: 1,500 XP
        Level 10: 5,500 XP
        Level 50: 127,500 XP
        Level 100: 505,000 XP
    """
    return int(100 * level * (level + 1) / 2)

# أسماء المستويات (100 مستوى)
LEVEL_NAMES = {
    # المستويات 1-10: المبتدئ
    (1, 10): {"name": "المبتدئ", "emoji": "🔰", "tier": "bronze"},
    
    # المستويات 11-20: الطالب
    (11, 20): {"name": "الطالب", "emoji": "📚", "tier": "bronze"},
    
    # المستويات 21-30: الدارس
    (21, 30): {"name": "الدارس", "emoji": "✏️", "tier": "silver"},
    
    # المستويات 31-40: المجتهد
    (31, 40): {"name": "المجتهد", "emoji": "📖", "tier": "silver"},
    
    # المستويات 41-50: النشيط
    (41, 50): {"name": "النشيط", "emoji": "⚡", "tier": "gold"},
    
    # المستويات 51-60: المثابر
    (51, 60): {"name": "المثابر", "emoji": "💪", "tier": "gold"},
    
    # المستويات 61-70: المتقدم
    (61, 70): {"name": "المتقدم", "emoji": "🔷", "tier": "platinum"},
    
    # المستويات 71-80: المتميز
    (71, 80): {"name": "المتميز", "emoji": "⭐", "tier": "platinum"},
    
    # المستويات 81-90: الخبير
    (81, 90): {"name": "الخبير", "emoji": "🔶", "tier": "diamond"},
    
    # المستويات 91-95: الماهر
    (91, 95): {"name": "الماهر", "emoji": "💎", "tier": "diamond"},
    
    # المستويات 96-99: الأسطورة
    (96, 99): {"name": "الأسطورة", "emoji": "👑", "tier": "legendary"},
    
    # المستوى 100: البطل
    (100, 100): {"name": "البطل الأعظم", "emoji": "🏆", "tier": "mythic"},
}

# رموز الـ Tiers (المراتب)
TIER_BADGES = {
    "bronze": "🥉",
    "silver": "🥈",
    "gold": "🥇",
    "platinum": "💠",
    "diamond": "💎",
    "legendary": "👑",
    "mythic": "✨",
    "beyond": "🌟"
}

def get_tier_badge(tier: str) -> str:
    """الحصول على شارة المرتبة"""
    return TIER_BADGES.get(tier, "📊")

def get_level_info_from_number(level: int) -> dict:
    """
    الحصول على معلومات المستوى من رقمه
    
    Returns:
        dict: {name, emoji, tier}
    """
    for (min_level, max_level), info in LEVEL_NAMES.items():
        if min_level <= level <= max_level:
            return info
    
    # إذا تجاوز 100
    return {"name": "ما وراء الأسطورة", "emoji": "✨", "tier": "beyond"}

def get_level_from_xp(xp: int) -> dict:
    """
    حساب المستوى بناءً على XP
    
    Returns:
        dict: معلومات المستوى الكاملة
    """
    # حساب المستوى الحالي
    current_level = 1
    for level in range(1, 101):  # حتى المستوى 100
        if xp >= calculate_xp_for_level(level):
            current_level = level
        else:
            break
    
    # معلومات المستوى
    level_info = get_level_info_from_number(current_level)
    
    # XP المطلوب للمستويات
    xp_current_level = calculate_xp_for_level(current_level) if current_level > 1 else 0
    
    # إذا وصل للمستوى 100
    if current_level >= 100:
        return {
            "level": current_level,
            "name": level_info["name"],
            "emoji": level_info["emoji"],
            "tier": level_info["tier"],
            "xp_current": xp,
            "xp_next": None,
            "progress_percent": 100,
            "max_level": True
        }
    
    # حساب XP في المستوى الحالي
    xp_next_level = calculate_xp_for_level(current_level + 1)
    xp_in_current_level = xp - xp_current_level
    xp_needed_for_next = xp_next_level - xp_current_level
    progress = (xp_in_current_level / xp_needed_for_next * 100)
    
    # معلومات المستوى التالي
    next_level_info = get_level_info_from_number(current_level + 1)
    
    return {
        "level": current_level,
        "name": level_info["name"],
        "emoji": level_info["emoji"],
        "tier": level_info["tier"],
        "xp_current": xp,
        "xp_next": xp_next_level,
        "xp_in_level": xp_in_current_level,
        "xp_needed": xp_needed_for_next,
        "progress_percent": round(progress, 1),
        "next_level": current_level + 1,
        "next_level_name": next_level_info["name"],
        "next_level_emoji": next_level_info["emoji"]
    }

