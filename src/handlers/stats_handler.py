"""
معالج الإحصائيات والتقدم
"""

from telegram import Update
from telegram.ext import ContextTypes
from src.database.db_manager import DatabaseManager
from src.database.repositories import UserRepository, StatsRepository
import config
from datetime import datetime

# إنشاء الاتصال بقاعدة البيانات
db_manager = DatabaseManager(config.DATABASE_PATH)
user_repo = UserRepository(db_manager)
stats_repo = StatsRepository(db_manager)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /stats
    عرض الإحصائيات الشخصية
    """
    user_id = update.effective_user.id
    
    # التحقق من وجود المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ لم تبدأ أي اختبار بعد!\n"
            "استخدم /start_quiz للبدء"
        )
        return
    
    # الحصول على الإحصائيات
    stats = stats_repo.get_user_stats(user_id)
    
    if not stats:
        await update.message.reply_text("❌ لا توجد إحصائيات متاحة")
        return
    
    # حساب عدد الأيام منذ الانضمام
    join_date = datetime.fromisoformat(stats['join_date'])
    days_since_join = (datetime.now() - join_date).days
    
    # تنسيق الرسالة
    message = f"""
📊 **إحصائياتك الشخصية**

👤 المستخدم: {update.effective_user.first_name}
📅 منذ الانضمام: {days_since_join} يوم

🔢 **الأسئلة:**
   • إجمالي الأسئلة: {stats['total_questions']}
   • الإجابات الصحيحة: {stats['correct_answers']}
   • نسبة الدقة: {stats['accuracy']:.1f}%

🎯 **الاختبارات:**
   • عدد الاختبارات: {stats['quiz_count']}
   • أفضل نتيجة: {stats['best_score']:.1f}%

"""
    
    # إضافة إحصائيات المواد
    if stats['subject_stats']:
        message += "📚 **حسب المادة:**\n"
        for subject_stat in stats['subject_stats']:
            subject_name = subject_stat['subject']
            count = subject_stat['count']
            avg = subject_stat['avg_score']
            message += f"   • {subject_name}: {count} اختبار (معدل {avg:.1f}%)\n"
    
    message += "\n💪 استمر في التقدم!"
    
    await update.message.reply_text(message)

async def progress_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /progress
    عرض التقدم في المواد والفصول
    """
    user_id = update.effective_user.id
    
    # التحقق من وجود المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        await update.message.reply_text(
            "❌ لم تبدأ أي اختبار بعد!\n"
            "استخدم /start_quiz للبدء"
        )
        return
    
    # الحصول على التقدم
    progress = stats_repo.get_subject_progress(user_id)
    
    if not progress:
        await update.message.reply_text("❌ لا يوجد تقدم للعرض بعد")
        return
    
    # تنسيق الرسالة
    message = "📈 **تقدمك في المواد:**\n\n"
    
    for subject, chapters in progress.items():
        message += f"📚 **{subject}**:\n"
        for chapter in chapters:
            emoji = "✅" if chapter['avg_score'] >= 80 else "🔄" if chapter['avg_score'] >= 60 else "📝"
            message += f"   {emoji} {chapter['chapter']}: "
            message += f"{chapter['attempts']} محاولة، معدل {chapter['avg_score']}%\n"
        message += "\n"
    
    message += "💡 **الرموز:**\n"
    message += "✅ ممتاز (80%+) | 🔄 جيد (60%+) | 📝 يحتاج تحسين\n"
    
    await update.message.reply_text(message)
