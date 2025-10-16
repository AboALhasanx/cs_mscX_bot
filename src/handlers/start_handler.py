"""
معالجات البداية والتعليمات - نسخة محدثة مع HTML وإحصائيات الأسبوع
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from src.utils.keyboards import main_menu_keyboard
from src.database.db_manager import DatabaseManager
from src.database.repositories import UserRepository, StatsRepository

# إنشاء الاتصال بقاعدة البيانات
db_manager = DatabaseManager(config.DATABASE_PATH)
user_repo = UserRepository(db_manager)
stats_repo = StatsRepository(db_manager)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /start
    رسالة ترحيب مخصصة + إحصائيات الأسبوع
    """
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # التأكد من وجود المستخدم
    user = user_repo.get_user(user_id)
    if not user:
        user = user_repo.create_user(user_id, username, first_name)
        is_new = True
    else:
        is_new = False
    
    # رسالة مخصصة
    if is_new:
        # مستخدم جديد
        message = f"""
<b>🎓 مرحباً بك {first_name}!</b>

أهلاً بك في <b>بوت اختبارات التنافسي</b> 🚀

هذا البوت سيساعدك على:
• التحضير للامتحان التنافسي
• اختبار معلوماتك في 6 مواد
• تتبع تقدمك وتحليل أدائك

<b>🎯 ابدأ الآن!</b>
اختر من الأزرار أدناه 👇
"""
    else:
        # مستخدم قديم - عرض إحصائيات الأسبوع
        weekly_stats = stats_repo.get_weekly_stats(user_id)
        
        # اختيار emoji حسب النشاط
        if weekly_stats['active_days'] >= 5:
            emoji = "🔥"
            status = "نشاط ممتاز!"
        elif weekly_stats['active_days'] >= 3:
            emoji = "💪"
            status = "نشاط جيد!"
        elif weekly_stats['total_questions'] > 0:
            emoji = "📚"
            status = "استمر بالتدريب"
        else:
            emoji = "🎯"
            status = "ابدأ رحلتك!"
        
        message = f"""
<b>👋 أهلاً {first_name}!</b>

{emoji} <b>إحصائياتك هذا الأسبوع:</b>

📝 عدد الأسئلة: <b>{weekly_stats['total_questions']}</b>
✅ الإجابات الصحيحة: <b>{weekly_stats['correct_answers']}</b>
📊 نسبة الدقة: <b>{weekly_stats['accuracy']:.1f}%</b>
📅 أيام نشاطك: <b>{weekly_stats['active_days']}/7</b>
🎯 عدد الاختبارات: <b>{weekly_stats['quiz_count']}</b>

"""
        
        # رسالة تحفيزية حسب الأداء
        if weekly_stats['total_questions'] == 0:
            message += "📚 <b>لم تحل أي اختبار هذا الأسبوع - ابدأ الآن!</b>\n\n"
        elif weekly_stats['accuracy'] >= 85:
            message += "🏆 <b>ممتاز! استمر على هذا الأداء الرائع!</b>\n\n"
        elif weekly_stats['accuracy'] >= 70:
            message += "👍 <b>جيد جداً! يمكنك الوصول للتميز بالمزيد من التدريب</b>\n\n"
        elif weekly_stats['accuracy'] >= 60:
            message += "💪 <b>جيد! راجع المواضيع الضعيفة لتحسين نتائجك</b>\n\n"
        else:
            message += "📖 <b>استمر بالتدريب - التحسّن يحتاج وقت!</b>\n\n"
        
        message += "<b>اختر من الأزرار أدناه:</b> 👇"
    
    await update.message.reply_html(
        message,
        reply_markup=main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /help
    عرض الأوامر المتاحة والمساعدة
    """
    help_text = """
<b>📚 الأوامر المتاحة:</b>

/start - الصفحة الرئيسية + إحصائيات الأسبوع
/stats - إحصائياتك الكاملة
/progress - تقدمك في المواد
/level - مستواك الحالي
/reload - تحديث الأسئلة من GitHub
/help - عرض هذه الرسالة

<b>🎯 كيف أبدأ؟</b>
1. اضغط /start
2. اختر المادة من الأزرار
3. اختر الفصل/الجزء
4. ابدأ الاختبار!

<b>💡 نصائح:</b>
• كل اختبار يحتوي على جميع أسئلة الفصل
• الشرح يظهر فوراً بعد كل إجابة
• يمكنك الخروج من الاختبار في أي وقت
• الإحصائيات تُحفظ تلقائياً
• اكسب XP لكل سؤال ترفع مستواك!

<b>📊 تتبع تقدمك:</b>
استخدم الأزرار في القائمة الرئيسية:
⭐ المستوى - 📊 الإحصائيات
📈 التقدم - 🏆 الإنجازات

<b>🎮 نظام المستويات:</b>
• كل سؤال صحيح = 10 XP
• كل سؤال خطأ = 2 XP (جائزة ترضية)
• نتيجة 100% = مكافأة 50 XP إضافية!
• كلما زاد XP، ترفع مستواك!

<b>🔄 تحديث الأسئلة:</b>
إذا أُضيفت أسئلة جديدة على GitHub، استخدم /reload

<i>بالتوفيق في التحضير للامتحان التنافسي! 🎓</i>
"""
    
    await update.message.reply_html(help_text)
