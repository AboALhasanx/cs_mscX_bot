"""
أزرار Telegram (Inline Keyboards)
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.constants.subjects import SUBJECTS

def main_menu_keyboard() -> InlineKeyboardMarkup:
    """القائمة الرئيسية - اختيار المادة"""
    keyboard = []
    
    # إضافة كل مادة كصف في الأزرار
    for subject_key, subject_data in SUBJECTS.items():
        button_text = f"{subject_data['emoji']} {subject_data['name_ar']}"
        keyboard.append([
            InlineKeyboardButton(button_text, callback_data=f"subject_{subject_key}")
        ])
    
    return InlineKeyboardMarkup(keyboard)

def chapters_keyboard(subject_key: str) -> InlineKeyboardMarkup:
    """قائمة الفصول لمادة معينة"""
    subject = SUBJECTS.get(subject_key)
    
    if not subject:
        return None
    
    keyboard = []
    
    # إضافة كل فصل
    for chapter_key, chapter_name in subject['chapters'].items():
        keyboard.append([
            InlineKeyboardButton(
                chapter_name, 
                callback_data=f"quiz_{subject_key}_{chapter_key}"
            )
        ])
    
    # زر العودة
    keyboard.append([
        InlineKeyboardButton("🔙 رجوع", callback_data="back_to_subjects")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def quiz_actions_keyboard() -> InlineKeyboardMarkup:
    """أزرار خيارات بعد الاختبار"""
    keyboard = [
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="show_stats")],
        [InlineKeyboardButton("🔄 اختبار جديد", callback_data="new_quiz")],
        [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")]
    ]
    
    return InlineKeyboardMarkup(keyboard)
