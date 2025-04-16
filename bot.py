from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from telegram import Update
import config
import logging
import sys

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout  # Force logs to show in console
)
logger = logging.getLogger(__name__)

async def start(update: Update, context):
    """Handle /start command with detailed response"""
    user = update.effective_user
    logger.info(f"Start command from {user.id} ({user.first_name})")
    
    await update.message.reply_markdown_v2(
        fr"""
🚀 *Bot Activated*  
Hello {user.mention_markdown_v2()}\!  
Your ID: `{user.id}`  
Bot status: ONLINE  
        
Try sending any message or /help
        """
    )

async def help_cmd(update: Update, context):
    """Handle /help command"""
    await update.message.reply_text(
        "🆘 Help Menu\n"
        "/start - Begin interaction\n"
        "/help - Show this message\n"
        "Any other text - Echo test"
    )

async def echo(update: Update, context):
    """Echo all text messages"""
    logger.info(f"Echoing message from {update.effective_user.id}")
    await update.message.reply_text(
        f"🔁 You said: {update.message.text}"
    )

async def debug_updates(update: Update, context):
    """Log all incoming updates"""
    logger.debug(f"Incoming update:\n{update.to_dict()}")

async def post_init(app):
    """Send startup notification"""
    try:
        await app.bot.send_message(
            chat_id=config.ADMIN_IDS[0],
            text=f"🤖 Bot started successfully!\n"
                 f"Python: {sys.version.split()[0]}\n"
                 f"Token: {app.bot.token[:6]}...{app.bot.token[-4:]}"
        )
    except Exception as e:
        logger.error(f"Startup message failed: {e}")

def main():
    try:
        logger.info(f"Starting bot with Python {sys.version}")
        
        # Build application with enhanced configuration
        app = (
            ApplicationBuilder()
            .token(config.TOKEN)
            .post_init(post_init)
            .connect_timeout(30)
            .read_timeout(30)
            .pool_timeout(30)
            .build()
        )

        # Set up handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_cmd))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Debug handler (captures ALL updates)
        app.add_handler(MessageHandler(filters.ALL, debug_updates), group=-1)

        logger.info("Bot initialized. Starting polling...")
        app.run_polling(
            poll_interval=0.5,
            timeout=20,
            drop_pending_updates=True
        )

    except Exception as e:
        logger.critical(f"Bot crashed: {e}", exc_info=True)
        print("\n🛠️ Troubleshooting Guide:")
        print("1. Verify token at https://api.telegram.org/botYOURTOKEN/getMe")
        print("2. Check .env file exists with TELEGRAM_BOT_TOKEN")
        print("3. Test with: python -c \"from telegram import Bot; print(Bot('YOURTOKEN').get_me())\"")
        print("4. Disable privacy via @BotFather: /setprivacy → Disable")

if __name__ == "__main__":
    # Clear terminal for better visibility
    print("\033[H\033[J", end="")
    main()