from telegram import Update, Poll
from telegram.ext import ContextTypes
import config
from src.services.question_service import QuestionService
from src.database.db_manager import DatabaseManager
from src.database.repositories import UserRepository, QuizRepository
import config

# إنشاء قاعدة البيانات
db_manager = DatabaseManager(config.DATABASE_PATH)
user_repo = UserRepository(db_manager)
quiz_repo = QuizRepository(db_manager)

# خدمة الأسئلة
question_service = QuestionService(config.QUESTIONS_DIR)

# تخزين جلسات المستخدمين (مؤقت في الذاكرة)
user_sessions = {}

async def start_quiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """بدء اختبار جديد"""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    try:
        # التأكد من وجود المستخدم في قاعدة البيانات
        user = user_repo.get_user(user_id)
        if not user:
            user = user_repo.create_user(user_id, username, first_name)
        
        # تحميل الأسئلة
        questions = question_service.load_questions('test_quiz.json')
        selected_questions = question_service.get_random_questions(
            questions, 
            config.QUESTIONS_PER_QUIZ
        )
        
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
            'total': len(selected_questions)
        }
        
        start_msg = config.QUIZ_START_MESSAGE.format(total=len(selected_questions))
        await update.message.reply_text(start_msg)
        
        await send_question(update, context, user_id)
        
    except Exception as e:
        logger.error(f"خطأ في بدء الاختبار: {e}")
        await update.message.reply_text(f"❌ حدث خطأ: {str(e)}")

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
        question=f"❓ السؤال {current_index + 1}/{len(questions)}:\n\n{question_data['question']}",
        options=question_data['options'],
        type=Poll.QUIZ,
        correct_option_id=question_data['correct_option_id'],
        explanation=question_data.get('explanation', ''),
        is_anonymous=False,
        open_period=60  # مفتوح لمدة 60 ثانية
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
    text = "صحيح!" if is_correct else "خطأ!"
    
    await context.bot.send_message(
        chat_id=user_id,
        text=f"{emoji} {text}\n\nالسؤال التالي قادم..."
    )
    
    # الانتظار ثانية واحدة
    import asyncio
    await asyncio.sleep(1.5)
    
    # إرسال السؤال التالي أو إنهاء الاختبار
    if session['current_question'] < len(session['questions']):
        # السؤال التالي
        next_q = session['questions'][session['current_question']]
        await context.bot.send_poll(
            chat_id=user_id,
            question=f"❓ السؤال {session['current_question'] + 1}/{session['total']}:\n\n{next_q['question']}",
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
    
    # تحديد الرسالة بناءً على النتيجة
    if score >= config.PASSING_SCORE:
        result_emoji = "🎉"
        result_text = "ممتاز! لقد نجحت في الاختبار"
    else:
        result_emoji = "📚"
        result_text = "حاول مرة أخرى - يمكنك تحسين نتيجتك!"
    
    result_message = config.QUIZ_FINISHED_MESSAGE.format(
        score=score,
        total=total,
        percentage=percentage,
        result_emoji=result_emoji,
        result_text=result_text
    )
    
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=result_message
    )
    
    # تحديث قاعدة البيانات
    quiz_repo.finish_session(session['session_id'], score)
    user_repo.update_stats(user_id, total, score)

    
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
    
    if score >= config.PASSING_SCORE:
        result_emoji = "🎉"
        result_text = "ممتاز! لقد نجحت في الاختبار"
    else:
        result_emoji = "📚"
        result_text = "حاول مرة أخرى - يمكنك تحسين نتيجتك!"
    
    result_message = config.QUIZ_FINISHED_MESSAGE.format(
        score=score,
        total=total,
        percentage=percentage,
        result_emoji=result_emoji,
        result_text=result_text
    )
    
    await context.bot.send_message(
        chat_id=user_id,
        text=result_message
    )
    
    del user_sessions[user_id]
