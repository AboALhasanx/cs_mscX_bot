"""
معالج الأزرار التفاعلية (Callback Queries)
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.utils.keyboards import main_menu_keyboard, chapters_keyboard
from src.constants.subjects import SUBJECTS, get_subject_name, get_subject_emoji
from src.handlers.quiz_handler import start_quiz_for_subject
import logging

logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج جميع الأزرار التفاعلية"""
    query = update.callback_query
    await query.answer()  # تأكيد استلام الضغطة
    
    data = query.data
    
    # اختيار مادة
    if data.startswith("subject_"):
        subject_key = data.replace("subject_", "")
        await show_chapters(query, subject_key)
    
    # بدء اختبار
    elif data.startswith("quiz_"):
        parts = data.split("_")
        subject_key = parts[1]
        chapter_key = parts[2]
        await start_quiz_for_subject(query, context, subject_key, chapter_key)
    
    # العودة للمواد
    elif data == "back_to_subjects":
        await query.edit_message_text(
            "اختر المادة:",
            reply_markup=main_menu_keyboard()
        )
    
    # القائمة الرئيسية
    elif data == "main_menu":
        await query.edit_message_text(
            "🏠 القائمة الرئيسية\n\nاختر المادة:",
            reply_markup=main_menu_keyboard()
        )
    
    # اختبار جديد
    elif data == "new_quiz":
        await query.edit_message_text(
            "اختر المادة:",
            reply_markup=main_menu_keyboard()
        )

async def show_chapters(query, subject_key: str):
    """عرض فصول المادة"""
    subject = SUBJECTS.get(subject_key)
    
    if not subject:
        await query.edit_message_text("❌ المادة غير موجودة")
        return
    
    message = f"{subject['emoji']} **{subject['name_ar']}**\n\nاختر الفصل:"
    
    await query.edit_message_text(
        message,
        reply_markup=chapters_keyboard(subject_key)
    )
