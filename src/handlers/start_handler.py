from telegram import Update
from telegram.ext import ContextTypes
import config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /start
    إرسال رسالة الترحيب
    """
    await update.message.reply_text(config.WELCOME_MESSAGE)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    معالج أمر /help
    عرض الأوامر المتاحة
    """
    await update.message.reply_text(config.HELP_MESSAGE)
