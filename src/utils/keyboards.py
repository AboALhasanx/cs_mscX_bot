"""
أزرار Telegram (Inline Keyboards) - نسخة محدثة
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.constants.subjects import SUBJECTS

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    القائمة الرئيسية - اختيار المادة + أزرار الإحصائيات
    """
    keyboard = []
    
    # قسم المواد
    for subject_key, subject_data in SUBJECTS.items():
        button_text = f"{subject_data['emoji']} {subject_data['name_ar']}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"subject_{subject_key}")
        ])
    
    # فاصل
    keyboard.append([InlineKeyboardButton("━━━━━━━━━━━━━━━", callback_data="separator")])
    
    # قسم الإحصائيات والملف الشخصي
    keyboard.append([
        InlineKeyboardButton("⭐ المستوى", callback_data="show_level"),
        InlineKeyboardButton("📊 الإحصائيات", callback_data="show_stats")
    ])
    
    keyboard.append([
        InlineKeyboardButton("📈 التقدم", callback_data="show_progress"),
        InlineKeyboardButton("🏆 الإنجازات", callback_data="show_achievements")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def parts_keyboard(subject_key: str, parts: list) -> InlineKeyboardMarkup:
    """
    قائمة الأجزاء لمادة معينة
    يعرض العنوان من metadata بدلاً من "الجزء 1"
    """
    keyboard = []
    
    # إضافة كل جزء
    for part in parts:
        # استخدام العنوان الحقيقي من metadata
        title = part.get('title_ar', part.get('display', f"الجزء {part['part_num']}"))
        button_text = f"📄 {title}"
        
        callback_data = f"quiz_{subject_key}_{part['part']}_{part['filepath']}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=callback_data)
        ])
    
    # زر العودة
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع للمواد", callback_data="back_to_subjects")
    ])
    
    return InlineKeyboardMarkup(keyboard)


def quiz_exit_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """
    زر الخروج من الاختبار
    """
    keyboard = [
        [InlineKeyboardButton("🚫 إنهاء الاختبار", callback_data=f"exit_quiz_{user_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def quiz_actions_keyboard() -> InlineKeyboardMarkup:
    """أزرار خيارات بعد الاختبار"""
    keyboard = [
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats")],
        [InlineKeyboardButton("🔄 اختبار جديد", callback_data="new_quiz")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    
    return InlineKeyboardMarkup(keyboard)
