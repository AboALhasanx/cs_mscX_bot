"""
معالج الأزرار التفاعلية - نسخة محدثة مع دعم metadata وHTML
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.utils.keyboards import main_menu_keyboard, parts_keyboard
from src.constants.subjects import SUBJECTS, get_subject_full_name
from src.handlers.quiz_handler import start_quiz_for_part, question_service, user_sessions, quiz_repo, user_repo
import config
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


from src.database.db_manager import DatabaseManager
import config

# إنشاء اتصال قاعدة البيانات للحذف
db_manager = DatabaseManager(config.DATABASE_PATH)


logger = logging.getLogger(__name__)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج جميع الأزرار التفاعلية"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = query.from_user.id
    
    # تجاهل الفاصل
    if data == "separator":
        return
    
    # اختيار مادة -> عرض الأجزاء
    if data.startswith("subject_"):
        subject_key = data.replace("subject_", "")
        await show_parts(query, context, subject_key)
    
    # بدء اختبار لجزء محدد
    elif data.startswith("quiz_"):
        parts = data.split("_", 3)
        if len(parts) >= 4:
            subject_key = parts[1]
            part_name = parts[2]
            filepath = parts[3]
            await start_quiz_for_part(query, context, subject_key, part_name, filepath)
    
    # الخروج من الاختبار
    elif data.startswith("exit_quiz_"):
        exit_user_id = int(data.replace("exit_quiz_", ""))
        await handle_exit_quiz(query, context, exit_user_id)
    
    # عرض المستوى
    elif data == "show_level":
        await show_level_callback(query, user_id)
    
    # عرض الإحصائيات
    elif data == "show_stats":
        await show_stats_callback(query, user_id)
    
    # عرض التقدم
    elif data == "show_progress":
        await show_progress_callback(query, user_id)
    
    # عرض الإنجازات
    elif data == "show_achievements":
        await show_achievements_callback(query, user_id)
    
    # العودة للمواد
    elif data == "back_to_subjects":
        await query.edit_message_text(
            "<b>اختر المادة:</b>",
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # القائمة الرئيسية
    elif data == "main_menu":
        await query.edit_message_text(
            "<b>🏠 القائمة الرئيسية</b>\n\nاختر المادة أو اعرض إحصائياتك:",
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )
    
    # اختبار جديد
    elif data == "new_quiz":
        await query.edit_message_text(
            "<b>اختر المادة:</b>",
            reply_markup=main_menu_keyboard(),
            parse_mode='HTML'
        )

async def show_parts(query, context: ContextTypes.DEFAULT_TYPE, subject_key: str):
    """
    عرض الأجزاء المتاحة للمادة
    يكتشف الملفات تلقائياً من GitHub ويعرض أسماءها من metadata
    """
    subject = SUBJECTS.get(subject_key)
    
    if not subject:
        await query.edit_message_text("❌ المادة غير موجودة")
        return
    
    # إرسال رسالة انتظار
    await query.edit_message_text(
        f"{subject['emoji']} <b>{subject['name_ar']}</b>\n\n"
        "⏳ جاري البحث عن الفصول المتاحة...",
        parse_mode='HTML'
    )
    
    # الحصول على اسم المجلد من config
    folder_name = config.SUBJECT_TO_FOLDER.get(subject_key)
    
    if not folder_name:
        await query.edit_message_text(
            f"❌ لم يتم تكوين المجلد للمادة: {subject['name_ar']}",
            parse_mode='HTML'
        )
        return
    
    # اكتشاف الأجزاء المتاحة
    parts = question_service.get_available_parts_from_github(subject_key, folder_name)
    
    if not parts:
        await query.edit_message_text(
            f"{subject['emoji']} <b>{subject['name_ar']}</b>\n\n"
            "❌ لا توجد فصول متاحة حالياً.\n\n"
            "تأكد من اتصالك بالإنترنت أو جرب مرة أخرى.",
            reply_markup=parts_keyboard(subject_key, []),
            parse_mode='HTML'
        )
        return
    
    # عرض الأجزاء
    message = f"{subject['emoji']} <b>{subject['name_ar']}</b>\n"
    message += f"<i>{subject['description']}</i>\n\n"
    message += f"✅ تم العثور على <b>{len(parts)}</b> فصل\n\n"
    message += "<b>اختر الفصل الذي تريد التدرب عليه:</b>"
    
    await query.edit_message_text(
        message,
        reply_markup=parts_keyboard(subject_key, parts),
        parse_mode='HTML'
    )

async def handle_exit_quiz(query, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    معالجة الخروج من الاختبار
    لا يحفظ النتيجة - فقط يلغي الاختبار
    """
    # التحقق من وجود جلسة نشطة
    if user_id not in user_sessions:
        await query.edit_message_text(
            "❌ <b>لا يوجد اختبار نشط حالياً.</b>",
            parse_mode='HTML'
        )
        return
    
    session = user_sessions[user_id]
    
    # حذف الجلسة من قاعدة البيانات (إلغاء تام)
    try:
        # حذف الجلسة من database بدون حفظ النتيجة
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM quiz_sessions WHERE session_id = ?', (session['session_id'],))
        cursor.execute('DELETE FROM question_attempts WHERE session_id = ?', (session['session_id'],))
        conn.commit()
        conn.close()
        
        logger.info(f"✅ تم إلغاء الجلسة {session['session_id']} للمستخدم {user_id}")
    except Exception as e:
        logger.error(f"خطأ في حذف الجلسة: {e}")
    
    # حذف الجلسة من الذاكرة
    del user_sessions[user_id]
    
    # رسالة التأكيد
    message = f"""
<b>⚠️ تم إلغاء الاختبار</b>

📊 <b>معلومات الجلسة الملغاة:</b>
• الأسئلة المجابة: {session['current_question']}/{session['total']}
• الإجابات الصحيحة: {session['score']}

<b>⚠️ ملاحظة هامة:</b>
<i>لم يتم حفظ هذا الاختبار في قاعدة البيانات.
النتائج لن تُحسب ضمن إحصائياتك.</i>

<b>ماذا تريد أن تفعل؟</b>
"""
    
    # العودة للقائمة الرئيسية
    await query.edit_message_text(
        message,
        reply_markup=main_menu_keyboard(),
        parse_mode='HTML'
    )

async def show_level_callback(query, user_id: int):
    """
    عرض معلومات المستوى عند الضغط على زر "⭐ المستوى"
    """
    from src.database.repositories import UserRepository
    from src.database.db_manager import DatabaseManager
    import config
    
    db_manager = DatabaseManager(config.DATABASE_PATH)
    user_repo = UserRepository(db_manager)
    
    # الحصول على المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await query.edit_message_text(
            "❌ <b>لم تبدأ أي اختبار بعد!</b>\n"
            "استخدم /start للبدء",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
            ]])
        )
        return
    
    # معلومات المستوى
    level_info = config.get_level_from_xp(user.xp)
    
    if 'max_level' in level_info:
        # أعلى مستوى
        message = f"""
<b>🏆 أعلى مستوى!</b>

{level_info['emoji']} <b>المستوى {level_info['level']}: {level_info['name']}</b>

• XP الكلي: <b>{level_info['xp_current']:,}</b>
• الأسئلة المحلولة: <b>{user.total_questions}</b>
• الدقة: <b>{user.accuracy:.1f}%</b>

<i>أنت وصلت لقمة النجاح! 👑</i>
"""
    else:
        # مستوى عادي
        progress_bar_length = 10
        filled = int(level_info['progress_percent'] / 10)
        empty = progress_bar_length - filled
        progress_bar = "━" * filled + "░" * empty
        
        message = f"""
<b>{level_info['emoji']} المستوى {level_info['level']}: {level_info['name']}</b>

{progress_bar} {level_info['progress_percent']}%

• XP: <b>{level_info['xp_in_level']:,} / {level_info['xp_needed']:,}</b>
• XP المتبقي: <b>{level_info['xp_needed'] - level_info['xp_in_level']:,}</b>
• الأسئلة المحلولة: <b>{user.total_questions}</b>
• الدقة: <b>{user.accuracy:.1f}%</b>

<b>المستوى التالي:</b>
{level_info['next_level_emoji']} <b>{level_info['next_level_name']}</b> (المستوى {level_info['level'] + 1})

<i>{config.get_random_motivational_message()}</i>
"""
    
    # أزرار العودة
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)

async def show_stats_callback(query, user_id: int):
    """
    عرض الإحصائيات عند الضغط على زر "📊 الإحصائيات"
    """
    from src.database.repositories import UserRepository, StatsRepository
    from src.database.db_manager import DatabaseManager
    import config
    from datetime import datetime
    
    db_manager = DatabaseManager(config.DATABASE_PATH)
    user_repo = UserRepository(db_manager)
    stats_repo = StatsRepository(db_manager)
    
    # الحصول على المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await query.edit_message_text(
            "❌ <b>لم تبدأ أي اختبار بعد!</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
            ]])
        )
        return
    
    # الحصول على الإحصائيات
    stats = stats_repo.get_user_stats(user_id)
    
    # حساب عدد الأيام منذ الانضمام
    join_date = datetime.fromisoformat(stats['join_date'])
    days_since_join = (datetime.now() - join_date).days
    
    # تنسيق الرسالة
    message = f"""
<b>📊 إحصائياتك الشخصية</b>

👤 <b>المستخدم:</b> {query.from_user.first_name}
📅 <b>منذ الانضمام:</b> {days_since_join} يوم

<b>🔢 الأسئلة:</b>
   • إجمالي الأسئلة: <b>{stats['total_questions']}</b>
   • الإجابات الصحيحة: <b>{stats['correct_answers']}</b>
   • نسبة الدقة: <b>{stats['accuracy']:.1f}%</b>

<b>🎯 الاختبارات:</b>
   • عدد الاختبارات: <b>{stats['quiz_count']}</b>
   • أفضل نتيجة: <b>{stats['best_score']:.1f}%</b>
"""
    
    # إضافة إحصائيات المواد
    if stats['subject_stats']:
        message += "\n<b>📚 حسب المادة:</b>\n"
        for subject_stat in stats['subject_stats']:
            subject_name = subject_stat['subject']
            count = subject_stat['count']
            avg = subject_stat['avg_score']
            message += f"   • {subject_name}: {count} اختبار (معدل {avg:.1f}%)\n"
    
    message += "\n💪 <i>استمر في التقدم!</i>"
    
    # أزرار العودة
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)

async def show_progress_callback(query, user_id: int):
    """
    عرض التقدم عند الضغط على زر "📈 التقدم"
    """
    from src.database.repositories import UserRepository, StatsRepository
    from src.database.db_manager import DatabaseManager
    import config
    
    db_manager = DatabaseManager(config.DATABASE_PATH)
    user_repo = UserRepository(db_manager)
    stats_repo = StatsRepository(db_manager)
    
    # الحصول على المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await query.edit_message_text(
            "❌ <b>لم تبدأ أي اختبار بعد!</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
            ]])
        )
        return
    
    # الحصول على التقدم
    progress = stats_repo.get_subject_progress(user_id)
    
    if not progress:
        await query.edit_message_text(
            "❌ <b>لا يوجد تقدم للعرض بعد</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
            ]])
        )
        return
    
    # تنسيق الرسالة
    message = "<b>📈 تقدمك في المواد:</b>\n\n"
    
    for subject, chapters in progress.items():
        message += f"<b>📚 {subject}:</b>\n"
        for chapter in chapters:
            emoji = "✅" if chapter['avg_score'] >= 80 else "🔄" if chapter['avg_score'] >= 60 else "📝"
            message += f"   {emoji} {chapter['chapter']}: "
            message += f"{chapter['attempts']} محاولة، معدل {chapter['avg_score']}%\n"
        message += "\n"
    
    message += "<b>💡 الرموز:</b>\n"
    message += "✅ ممتاز (80%+) | 🔄 جيد (60%+) | 📝 يحتاج تحسين"
    
    # أزرار العودة
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)

async def show_achievements_callback(query, user_id: int):
    """
    عرض الإنجازات عند الضغط على زر "🏆 الإنجازات"
    """
    from src.database.repositories import UserRepository
    from src.database.db_manager import DatabaseManager
    import config
    
    db_manager = DatabaseManager(config.DATABASE_PATH)
    user_repo = UserRepository(db_manager)
    
    # الحصول على المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await query.edit_message_text(
            "❌ <b>لم تبدأ أي اختبار بعد!</b>",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="main_menu")
            ]])
        )
        return
    
    # قائمة الإنجازات (ديناميكية)
    achievements = []
    
    # الإنجاز 1: المبتدئ
    if user.total_questions >= 10:
        achievements.append("✅ <b>المبتدئ</b> - حل 10 أسئلة على الأقل")
    else:
        achievements.append(f"🔒 <b>المبتدئ</b> - حل 10 أسئلة ({user.total_questions}/10)")
    
    # الإنجاز 2: الدقة العالية
    if user.accuracy >= 80 and user.total_questions >= 20:
        achievements.append("✅ <b>الدقيق</b> - دقة 80%+ في 20 سؤال")
    else:
        achievements.append(f"🔒 <b>الدقيق</b> - دقة 80%+ في 20 سؤال ({user.accuracy:.1f}%)")
    
    # الإنجاز 3: المثابر
    if user.total_questions >= 100:
        achievements.append("✅ <b>المثابر</b> - حل 100 سؤال")
    else:
        achievements.append(f"🔒 <b>المثابر</b> - حل 100 سؤال ({user.total_questions}/100)")
    
    # الإنجاز 4: الخبير
    if user.total_questions >= 500:
        achievements.append("✅ <b>الخبير</b> - حل 500 سؤال")
    else:
        achievements.append(f"🔒 <b>الخبير</b> - حل 500 سؤال ({user.total_questions}/500)")
    
    # الإنجاز 5: المستوى المتقدم
    level_info = config.get_level_from_xp(user.xp)
    if level_info['level'] >= 5:
        achievements.append(f"✅ <b>المتقدم</b> - الوصول للمستوى 5+")
    else:
        achievements.append(f"🔒 <b>المتقدم</b> - الوصول للمستوى 5 (حالياً: {level_info['level']})")
    
    # تنسيق الرسالة
    message = "<b>🏆 إنجازاتك</b>\n\n"
    
    unlocked = sum(1 for a in achievements if a.startswith("✅"))
    total = len(achievements)
    
    message += f"<b>مفتوح:</b> {unlocked}/{total}\n\n"
    
    for achievement in achievements:
        message += f"{achievement}\n"
    
    message += f"\n<i>استمر في التقدم لفتح المزيد! 🚀</i>"
    
    # أزرار العودة
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="main_menu")]
    ])
    
    await query.edit_message_text(message, parse_mode='HTML', reply_markup=keyboard)
