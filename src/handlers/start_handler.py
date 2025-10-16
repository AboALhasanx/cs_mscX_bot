"""
معالجات البداية والتعليمات
"""

from telegram import Update
from telegram.ext import ContextTypes
import config
from src.utils.keyboards import main_menu_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /start
    إرسال رسالة الترحيب + قائمة المواد
    """
    message = f"""
🎓 **مرحباً {update.effective_user.first_name}!**

أهلاً بك في بوت اختبارات التنافسي للماجستير

اختر المادة التي تريد التدرب عليها:
"""
    
    await update.message.reply_text(
        message,
        reply_markup=main_menu_keyboard()
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /help
    عرض الأوامر المتاحة
    """
    help_text = """
📚 **الأوامر المتاحة:**

/start - القائمة الرئيسية
/stats - إحصائياتك الشخصية
/progress - تقدمك في المواد
/help - عرض هذه الرسالة

**كيف أبدأ؟**
1. اضغط /start
2. اختر المادة
3. اختر الفصل
4. ابدأ الاختبار!

💡 كل اختبار يحتوي على 5 أسئلة عشوائية
"""
    
    await update.message.reply_text(help_text)
