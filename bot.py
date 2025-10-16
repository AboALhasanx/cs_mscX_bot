import logging
from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    PollAnswerHandler,
    CallbackQueryHandler
)
import config
from src.handlers.start_handler import start_command, help_command
from src.handlers.quiz_handler import handle_poll_answer
from src.handlers.stats_handler import stats_command, progress_command
from src.handlers.callback_handler import handle_callback

# إعداد Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    if not config.BOT_TOKEN:
        logger.error("❌ Bot Token غير موجود! تأكد من ملف .env")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # تسجيل المعالجات (Handlers)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("progress", progress_command))
    
    # معالج الأزرار التفاعلية
    application.add_handler(CallbackQueryHandler(handle_callback))
    
    # معالج إجابات الاختبار
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    
    # بدء البوت
    logger.info("🤖 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
    logger.info("📱 الأوامر المتاحة: /start /stats /progress /help")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
