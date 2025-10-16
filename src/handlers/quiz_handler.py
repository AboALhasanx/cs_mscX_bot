"""
معالج الاختبارات - نسخة محدّثة مع HTML ودعم metadata وزر الخروج ونظام XP
"""

from telegram import Update, Poll
from telegram.ext import ContextTypes
import config
from src.services.question_service import QuestionService
from src.database.db_manager import DatabaseManager
from src.database.repositories import UserRepository, QuizRepository
from src.constants.subjects import get_subject_name, get_subject_emoji
from src.utils.keyboards import quiz_exit_keyboard
import logging
import asyncio

logger = logging.getLogger(__name__)

# خدمة الأسئلة
question_service = QuestionService(
    questions_dir=config.QUESTIONS_DIR,
    github_url=config.GITHUB_RAW_URL,
    use_online=config.USE_ONLINE_QUESTIONS,
    cache_enabled=config.CACHE_QUESTIONS,
    cache_duration=config.CACHE_DURATION_MINUTES
)

# قاعدة البيانات
db_manager = DatabaseManager(config.DATABASE_PATH)
user_repo = UserRepository(db_manager)
quiz_repo = QuizRepository(db_manager)

# تخزين جلسات المستخدمين (مؤقت في الذاكرة)
user_sessions = {}

async def start_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /start_quiz (الاختبار التجريبي القديم)
    هذا للتوافق مع الإصدار السابق
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        # التأكد من وجود المستخدم
        user = user_repo.get_user(user_id)
        if not user:
            user = user_repo.create_user(user_id, username, first_name)
        
        # تحميل الأسئلة التجريبية
        try:
            questions_data = question_service.load_questions_for_part('test', 'test_quiz.json')
            # استخراج الأسئلة من البيانات
            if isinstance(questions_data, dict) and 'questions' in questions_data:
                questions = questions_data['questions']
            else:
                questions = questions_data  # صيغة قديمة
        except Exception as e:
            logger.error(f"فشل تحميل الأسئلة التجريبية: {e}")
            await update.message.reply_html(
                "❌ <b>عذراً، لا توجد أسئلة تجريبية متاحة.</b>\n\n"
                "استخدم /start لاختيار مادة محددة."
            )
            return

        # اختيار الأسئلة
        if config.USE_ALL_QUESTIONS:
            selected_questions = question_service.shuffle_all_questions(questions)
        else:
            selected_questions = question_service.get_random_questions(
                questions, 
                config.QUESTIONS_PER_QUIZ
            )
            for i in range(len(selected_questions)):
                selected_questions[i] = question_service.shuffle_question_options(selected_questions[i])
        
        # إنشاء جلسة في قاعدة البيانات
        session_id = quiz_repo.create_session(
            user_id=user_id,
            subject='test',
            chapter='general',
            total_questions=len(selected_questions)
        )
        
        # حفظ الجلسة في الذاكرة
        user_sessions[user_id] = {
            'session_id': session_id,
            'questions': selected_questions,
            'current_question': 0,
            'score': 0,
            'total': len(selected_questions),
            'subject': 'test',
            'chapter': 'general'
        }
        
        start_msg = config.QUIZ_START_MESSAGE.format(total=len(selected_questions))
        await update.message.reply_html(start_msg)
        
        await send_question(update, context, user_id)
        
    except Exception as e:
        logger.error(f"خطأ في بدء الاختبار: {e}")
        await update.message.reply_html(f"❌ <b>حدث خطأ:</b> {str(e)}")

async def start_quiz_for_part(query, context: ContextTypes.DEFAULT_TYPE, 
                               subject_key: str, part_name: str, filepath: str):
    """
    بدء اختبار لجزء محدد من مادة
    
    Args:
        subject_key: مفتاح المادة (مثل 'ai')
        part_name: اسم الجزء (مثل 'pt1')
        filepath: المسار الكامل للملف على GitHub
    """
    user_id = query.from_user.id
    username = query.from_user.username
    first_name = query.from_user.first_name
    
    try:
        # التأكد من وجود المستخدم
        user = user_repo.get_user(user_id)
        if not user:
            user = user_repo.create_user(user_id, username, first_name)
        
        # تحميل الأسئلة من GitHub
        questions_data = question_service.load_questions_for_part(subject_key, filepath)
        
        # استخراج metadata والأسئلة
        if isinstance(questions_data, dict):
            metadata = questions_data.get('metadata', {})
            questions_list = questions_data.get('questions', [])
        else:
            # صيغة قديمة (مصفوفة مباشرة)
            metadata = {'title_ar': part_name.upper().replace('PT', 'الجزء ')}
            questions_list = questions_data
        
        # اختيار الأسئلة (كلها أو عدد محدد)
        if config.USE_ALL_QUESTIONS:
            # استخدام جميع الأسئلة
            selected_questions = question_service.shuffle_all_questions(questions_list)
            logger.info(f"✅ سيتم استخدام جميع الأسئلة: {len(selected_questions)}")
        else:
            # اختيار عدد محدد
            selected_questions = question_service.get_random_questions(
                questions_list, 
                config.QUESTIONS_PER_QUIZ
            )
            # خلط خيارات الأسئلة المختارة
            for i in range(len(selected_questions)):
                selected_questions[i] = question_service.shuffle_question_options(selected_questions[i])
        
        # إنشاء جلسة
        session_id = quiz_repo.create_session(
            user_id=user_id,
            subject=subject_key,
            chapter=part_name,
            total_questions=len(selected_questions)
        )
        
        # حفظ الجلسة
        user_sessions[user_id] = {
            'session_id': session_id,
            'questions': selected_questions,
            'current_question': 0,
            'score': 0,
            'total': len(selected_questions),
            'subject': subject_key,
            'chapter': part_name,
            'metadata': metadata
        }
        
        # رسالة البداية
        subject_name = get_subject_name(subject_key)
        subject_emoji = get_subject_emoji(subject_key)
        chapter_title = metadata.get('title_ar', metadata.get('title', part_name.upper()))
        
        start_msg = f"""
<b>🚀 بدأ الاختبار!</b>

{subject_emoji} <b>المادة:</b> {subject_name}
📖 <b>الفصل:</b> {chapter_title}
🔢 <b>عدد الأسئلة:</b> {len(selected_questions)}

<i>جاهز؟ السؤال الأول قادم...</i>
"""
        
        await query.edit_message_text(start_msg, parse_mode='HTML')
        
        # الانتظار قليلاً
        await asyncio.sleep(1)
        
        # إرسال السؤال الأول
        first_q = selected_questions[0]
        await context.bot.send_poll(
            chat_id=user_id,
            question=f"Q1/{len(selected_questions)}: {first_q['question'][:250]}",
            options=first_q['options'],
            type=Poll.QUIZ,
            correct_option_id=first_q['correct_option_id'],
            explanation=first_q.get('explanation', ''),
            is_anonymous=False
        )
        
        # إرسال زر الخروج
        await context.bot.send_message(
            chat_id=user_id,
            text="<i>💡 لإنهاء الاختبار في أي وقت، اضغط الزر أدناه:</i>",
            reply_markup=quiz_exit_keyboard(user_id),
            parse_mode='HTML'
        )
        
    except (ConnectionError, ValueError) as e:
        logger.error(f"❌ فشل تحميل الأسئلة: {e}")
        await query.edit_message_text(
            "<b>❌ عذراً، فشل تحميل الأسئلة!</b>\n\n"
            "تأكد من اتصالك بالإنترنت وحاول مرة أخرى.",
            parse_mode='HTML'
        )
    except Exception as e:
        logger.error(f"❌ خطأ غير متوقع: {e}")
        await query.edit_message_text(
            f"<b>❌ حدث خطأ:</b> {str(e)}",
            parse_mode='HTML'
        )

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    إرسال السؤال الحالي كـ Telegram Quiz
    """
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    current_index = session['current_question']
    questions = session['questions']
    
    if current_index >= len(questions):
        # انتهى الاختبار
        await finish_quiz(update, context, user_id)
        return
    
    question_data = questions[current_index]
    
    # إرسال السؤال كـ Poll
    await context.bot.send_poll(
        chat_id=update.effective_chat.id,
        question=f"Q{current_index + 1}/{len(questions)}: {question_data['question'][:250]}",
        options=question_data['options'],
        type=Poll.QUIZ,
        correct_option_id=question_data['correct_option_id'],
        explanation=question_data.get('explanation', ''),
        is_anonymous=False,
        open_period=60
    )
    
    # إرسال زر الخروج إذا كان أول سؤال
    if current_index == 0:
        await context.bot.send_message(
            chat_id=user_id,
            text="<i>💡 لإنهاء الاختبار في أي وقت، اضغط الزر أدناه:</i>",
            reply_markup=quiz_exit_keyboard(user_id),
            parse_mode='HTML'
        )

async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالجة إجابة المستخدم على السؤال
    """
    user_id = update.poll_answer.user.id
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    # الحصول على الإجابة المختارة
    selected_option = update.poll_answer.option_ids[0]
    
    # الحصول على السؤال الحالي
    current_index = session['current_question']
    question_data = session['questions'][current_index]
    correct_answer = question_data['correct_option_id']
    
    # التحقق من صحة الإجابة
    is_correct = (selected_option == correct_answer)
    
    # تحديث النقاط
    if is_correct:
        session['score'] += 1
    
    # حفظ المحاولة في قاعدة البيانات
    quiz_repo.save_attempt(
        session_id=session['session_id'],
        question_text=question_data['question'],
        user_answer=selected_option,
        correct_answer=correct_answer,
        is_correct=is_correct
    )
    
    # الانتقال للسؤال التالي
    session['current_question'] += 1
    
    # إرسال رسالة تأكيد
    emoji = "✅" if is_correct else "❌"
    text = "<b>صحيح!</b>" if is_correct else "<b>خطأ!</b>"
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"{emoji} {text}\n\n<i>السؤال التالي قادم...</i>",
        parse_mode='HTML'
    )
    
    # الانتظار ثانية ونصف
    await asyncio.sleep(1.5)
    
    # إرسال السؤال التالي أو إنهاء الاختبار
    if session['current_question'] < len(session['questions']):
        # السؤال التالي
        next_q = session['questions'][session['current_question']]
        await context.bot.send_poll(
            chat_id=user_id,
            question=f"Q{session['current_question'] + 1}/{session['total']}: {next_q['question'][:250]}",
            options=next_q['options'],
            type=Poll.QUIZ,
            correct_option_id=next_q['correct_option_id'],
            explanation=next_q.get('explanation', ''),
            is_anonymous=False
        )
    else:
        # انتهى الاختبار
        await finish_quiz_after_answer(context, user_id)

async def finish_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    إنهاء الاختبار وعرض النتيجة (يُستدعى من send_question)
    """
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    score = session['score']
    total = session['total']
    percentage = round((score / total) * 100)
    
    # حساب XP المكتسب
    xp_earned = calculate_xp(score, total)
    
    # تحديث قاعدة البيانات
    quiz_repo.finish_session(session['session_id'], score)
    level_info = user_repo.add_xp(user_id, xp_earned)
    user_repo.update_stats(user_id, total, score, xp_earned)
    
    # إنشاء رسالة النتيجة
    result_message = create_result_message(score, total, percentage, xp_earned, level_info)
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result_message,
        parse_mode='HTML'
    )
    
    # حذف الجلسة
    del user_sessions[user_id]

async def finish_quiz_after_answer(context: ContextTypes.DEFAULT_TYPE, user_id: int):
    """
    إنهاء الاختبار بعد آخر إجابة (يُستدعى من handle_poll_answer)
    """
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    score = session['score']
    total = session['total']
    percentage = round((score / total) * 100)
    
    # حساب XP المكتسب
    xp_earned = calculate_xp(score, total)
    
    # تحديث قاعدة البيانات
    quiz_repo.finish_session(session['session_id'], score)
    level_info = user_repo.add_xp(user_id, xp_earned)
    user_repo.update_stats(user_id, total, score, xp_earned)
    
    # إنشاء رسالة النتيجة
    result_message = create_result_message(score, total, percentage, xp_earned, level_info)
    
    await context.bot.send_message(
        chat_id=user_id,
        text=result_message,
        parse_mode='HTML'
    )
    
    # حذف الجلسة
    del user_sessions[user_id]

def calculate_xp(score: int, total: int) -> int:
    """
    حساب XP المكتسب من الاختبار
    """
    xp = 0
    # XP من الإجابات الصحيحة
    xp += score * config.XP_PER_CORRECT_ANSWER
    # XP من الإجابات الخاطئة (جائزة ترضية)
    xp += (total - score) * config.XP_PER_WRONG_ANSWER
    
    # مكافأة إضافية إذا 100%
    if score == total:
        xp += config.XP_BONUS_PERFECT_QUIZ
    
    return xp

def create_result_message(score: int, total: int, percentage: float, 
                          xp_earned: int, level_info: dict) -> str:
    """
    إنشاء رسالة النتيجة مع معلومات المستوى
    """
    # رسالة مخصصة حسب النتيجة
    result_emoji, result_text = config.get_result_message(percentage)
    
    # رسالة تحفيزية عشوائية
    motivational = config.get_random_motivational_message()
    
    # رسالة النتيجة الأساسية
    message = f"""
<b>✅ انتهى الاختبار!</b>

📊 <b>النتيجة:</b> {score}/{total}
📈 <b>النسبة:</b> {percentage}%

{result_emoji} <b>{result_text}</b>

⭐ <b>XP المكتسب:</b> +{xp_earned} XP
"""
    
    # إضافة رسالة ترقية المستوى
    if level_info['leveled_up']:
        new_level_data = config.get_level_from_xp(level_info['total_xp'])
        message += f"""
🎉 <b>ترقية! مستوى جديد!</b>

{new_level_data['emoji']} <b>المستوى {new_level_data['level']}: {new_level_data['name']}</b>

"""
    
    # عرض معلومات المستوى الحالي
    current_level = config.get_level_from_xp(level_info['total_xp'])
    
    if 'max_level' not in current_level:
        # حساب شريط التقدم
        progress_bar_length = 10
        filled = int(current_level['progress_percent'] / 10)
        empty = progress_bar_length - filled
        progress_bar = "━" * filled + "░" * empty
        
        message += f"""
<b>المستوى الحالي:</b>
{current_level['emoji']} {current_level['name']} (المستوى {current_level['level']})

{progress_bar} {current_level['progress_percent']}%

• XP: {current_level['xp_in_level']:,} / {current_level['xp_needed']:,}
• الأسئلة المحلولة: {total}
• الدقة: {percentage}%

<b>المستوى التالي:</b> {current_level['next_level_emoji']} {current_level['next_level_name']}
"""
    else:
        message += f"""
🏆 <b>أعلى مستوى!</b>
{current_level['emoji']} {current_level['name']} - المستوى {current_level['level']}

أنت وصلت لقمة النجاح! 👑
"""
    
    message += f"\n<i>{motivational}</i>\n\n"
    message += "<i>اكتب /start للعودة للقائمة الرئيسية</i>"
    
    return message
