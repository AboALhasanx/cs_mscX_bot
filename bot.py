import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, PollAnswerHandler
import config
from src.handlers.start_handler import start_command, help_command
from src.handlers.quiz_handler import start_quiz_command, handle_poll_answer

# إعداد Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """الدالة الرئيسية لتشغيل البوت"""
    
    # التحقق من وجود Bot Token
    if not config.BOT_TOKEN:
        logger.error("❌ Bot Token غير موجود! تأكد من ملف .env")
        return
    
    # إنشاء التطبيق
    application = Application.builder().token(config.BOT_TOKEN).build()
    
    # تسجيل المعالجات (Handlers)
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("start_quiz", start_quiz_command))
    application.add_handler(PollAnswerHandler(handle_poll_answer))
    
    # بدء البوت
    logger.info("🤖 البوت يعمل الآن... اضغط Ctrl+C للإيقاف")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
