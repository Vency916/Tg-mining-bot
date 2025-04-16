from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler, JobQueue
from telegram.error import Conflict
from dotenv import load_dotenv
import os
import logging
import asyncio
from datetime import datetime, time
import random
import sys
import json
import httpx

# Load configuration
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TON_API_KEY = os.getenv('TON_API_KEY')
ADMIN_WALLET = os.getenv('ADMIN_WALLET')
ADMIN_IDS = [90907898]  # Your numeric chat ID

# Mining configuration
MINING_RATE = 0.0001
BASE_HASHRATE = 640.4
PAYOUT_THRESHOLD = 0.0356
TASK_REWARDS = {
    'join_channel': 5.0,
    'follow_twitter': 10.0,
    'invite_friends': 25.0
}

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class Miner:
    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username
        self.hashrate = BASE_HASHRATE
        self.balance = 0.0
        self.unconfirmed = 0.0
        self.wallet_address = None
        self.is_mining = False
        self.last_payout = datetime.now()
        self.blocks_found = 0
        self.completed_tasks = {task: False for task in TASK_REWARDS}
        self.last_task_reset = datetime.now()
        self.referrals = 0
        self.referral_earnings = 0.0

    async def start_mining(self):
        self.is_mining = True
        while self.is_mining:
            await asyncio.sleep(1)
            mined = MINING_RATE * (self.hashrate / BASE_HASHRATE)
            self.unconfirmed += mined
            if random.random() < 0.0001:
                self.blocks_found += 1
                self.unconfirmed += 0.5

    def get_dashboard(self):
        return (
            f"*💰 Confirmed Balance*: {self.balance:.4f} MINE\n"
            f"*⏳ Unconfirmed*: {self.unconfirmed:.4f} MINE\n"
            f"*⚡ Hashrate*: {self.hashrate} MH/s\n"
            f"*🔄 Payout*: {'✅ Ready' if self.unconfirmed >= PAYOUT_THRESHOLD and self.wallet_address else '❌ Needs wallet' if not self.wallet_address else '⏳ Pending'}"
        )

    def check_task_reset(self):
        """Reset tasks if it's a new day"""
        if datetime.now().date() > self.last_task_reset.date():
            self.completed_tasks = {task: False for task in TASK_REWARDS}
            self.last_task_reset = datetime.now()
            return True
        return False

async def reset_daily_tasks(context: CallbackContext):
    """Reset all tasks at midnight"""
    for miner in context.bot_data['miners'].values():
        miner.completed_tasks = {task: False for task in TASK_REWARDS}
        miner.last_task_reset = datetime.now()
    logger.info("Daily tasks reset for all users")

async def error_handler(update: object, context: CallbackContext) -> None:
    logger.error(f"Error: {context.error}", exc_info=context.error)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    context.bot_data.setdefault('miners', {})
    
    if user.id not in context.bot_data['miners']:
        context.bot_data['miners'][user.id] = Miner(user.id, user.username)
    
    miner = context.bot_data['miners'][user.id]
    miner.check_task_reset()
    
    keyboard = [
        ["⛏ Mine", "💰 Balance"],
        ["💳 Connect Wallet", "🔄 Payout"],
        ["✅ Daily Tasks"]
    ]
    
    await update.message.reply_text(
        f"*🚀 SMINE Mining Bot*\n\n"
        f"Welcome {user.first_name}!\n\n"
        f"{miner.get_dashboard()}",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def connect_wallet(update: Update, context: CallbackContext):
    miner = context.bot_data['miners'].get(update.effective_user.id)
    if not miner:
        return await update.message.reply_text("Please /start first")
    
    if len(context.args) < 1:
        return await update.message.reply_text("Usage: /connect YOUR_WALLET_ADDRESS")
    
    miner.wallet_address = context.args[0]
    await update.message.reply_text(
        "✅ Wallet connected!\nYou can now receive payouts",
        parse_mode='Markdown'
    )

async def handle_buttons(update: Update, context: CallbackContext):
    text = update.message.text
    miner = context.bot_data['miners'].get(update.effective_user.id)
    if not miner:
        return await update.message.reply_text("Please /start first")
    
    if text == "⛏ Mine":
        keyboard = [
            [InlineKeyboardButton("▶ Start", callback_data='start_mine')],
            [InlineKeyboardButton("⏹ Stop", callback_data='stop_mine')]
        ]
        status = "🟢 Active" if miner.is_mining else "🔴 Inactive"
        await update.message.reply_text(
            f"*⛏ Mining Control*\nStatus: {status}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif text == "💰 Balance":
        await update.message.reply_text(
            miner.get_dashboard(),
            parse_mode='Markdown'
        )
    
    elif text == "💳 Connect Wallet":
        await update.message.reply_text(
            "To connect your wallet:\n\n"
            "1. Open @wallet bot\n"
            "2. Create/get your wallet address\n"
            "3. Reply with:\n"
            "`/connect YOUR_WALLET_ADDRESS`\n\n"
            "This enables payouts to your wallet",
            parse_mode='Markdown'
        )
    
    elif text == "🔄 Payout":
        if not miner.wallet_address:
            return await update.message.reply_text("⚠️ Connect wallet first!")
        if miner.unconfirmed < PAYOUT_THRESHOLD:
            return await update.message.reply_text(
                f"Minimum payout: {PAYOUT_THRESHOLD} MINE\n"
                f"Your unconfirmed: {miner.unconfirmed:.4f} MINE",
                parse_mode='Markdown'
            )
        
        payout_amount = miner.unconfirmed
        miner.balance += payout_amount
        miner.unconfirmed = 0.0
        miner.last_payout = datetime.now()
        
        await update.message.reply_text(
            f"✅ {payout_amount:.4f} MINE paid to your wallet!",
            parse_mode='Markdown'
        )
    
    elif text == "✅ Daily Tasks":
        await show_tasks_menu(update, miner)

async def show_tasks_menu(update: Update, miner: Miner):
    """Display the daily tasks menu"""
    miner.check_task_reset()
    
    task_items = [
        ("Join Telegram Channel", "join_channel", 5.0, miner.completed_tasks['join_channel']),
        ("Follow on Twitter", "follow_twitter", 10.0, miner.completed_tasks['follow_twitter']),
        ("Invite 3 Friends", "invite_friends", 25.0, miner.completed_tasks['invite_friends'])
    ]
    
    keyboard = []
    for name, task_id, reward, completed in task_items:
        status = "✅" if completed else "🔘"
        keyboard.append([InlineKeyboardButton(
            f"{status} {name} (+{reward} MINE)",
            callback_data=f"task_{task_id}")])
    
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    await update.message.reply_text(
        "*🎯 Daily Tasks*\n\nComplete tasks to earn extra MINE tokens!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def button_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    miner = context.bot_data['miners'].get(query.from_user.id)
    if not miner:
        return
    
    data = query.data
    
    if data == 'start_mine' and not miner.is_mining:
        asyncio.create_task(miner.start_mining())
        await query.edit_message_text(
            "⛏ Mining started at 640.4 MH/s",
            reply_markup=query.message.reply_markup
        )
    elif data == 'stop_mine' and miner.is_mining:
        miner.is_mining = False
        await query.edit_message_text(
            "🛑 Mining stopped",
            reply_markup=query.message.reply_markup
        )
    elif data == 'back_to_main':
        keyboard = [
            ["⛏ Mine", "💰 Balance"],
            ["💳 Connect Wallet", "🔄 Payout"],
            ["✅ Daily Tasks"]
        ]
        await query.edit_message_text(
            miner.get_dashboard(),
            reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True),
            parse_mode='Markdown'
        )
    elif data.startswith('task_'):
        task_id = data[5:]  # Remove 'task_' prefix
        await handle_task_claim(query, miner, task_id)

async def handle_task_claim(query, miner: Miner, task_id: str):
    """Process a task claim request"""
    if task_id not in TASK_REWARDS:
        return await query.answer("Invalid task", show_alert=True)
    
    if miner.completed_tasks[task_id]:
        return await query.answer("You've already claimed this today!", show_alert=True)
    
    # Verify task completion
    verification = await verify_task_completion(miner.user_id, task_id)
    
    if not verification['success']:
        return await query.answer(verification['message'], show_alert=True)
    
    # Reward the user
    reward = TASK_REWARDS[task_id]
    miner.balance += reward
    miner.completed_tasks[task_id] = True
    
    # Update the message
    await show_tasks_menu(query, miner)
    await query.answer(f"🎉 +{reward} MINE earned!", show_alert=True)

async def verify_task_completion(user_id: int, task_id: str) -> dict:
    """Verify if user completed the task"""
    # Placeholder implementation - replace with actual checks:
    # - For join_channel: Check Telegram channel membership
    # - For follow_twitter: Check Twitter API
    # - For invite_friends: Check referral count
    return {'success': True, 'message': 'Task verified'}

async def handle_web_app_data(update: Update, context: CallbackContext):
    """Handle data from the Telegram Mini App"""
    try:
        data = json.loads(update.message.web_app_data.data)
        user_id = update.effective_user.id
        miner = context.bot_data['miners'].get(user_id)
        
        if not miner:
            return await update.message.reply_text("Please /start first")
        
        if data.get('action') == 'claim_task':
            task_id = data['taskId']
            if task_id not in TASK_REWARDS:
                return await update.message.reply_text("Invalid task")
            
            if miner.completed_tasks[task_id]:
                return await update.message.reply_text("Task already claimed")
            
            verification = await verify_task_completion(user_id, task_id)
            if not verification['success']:
                return await update.message.reply_text(verification['message'])
            
            reward = TASK_REWARDS[task_id]
            miner.balance += reward
            miner.completed_tasks[task_id] = True
            
            await context.bot.send_message(
                chat_id=user_id,
                text=json.dumps({
                    'action': 'task_completed',
                    'taskId': task_id,
                    'reward': reward,
                    'balance': miner.balance
                })
            )
            
    except Exception as e:
        logger.error(f"Web app data error: {e}")
        await update.message.reply_text("❌ Error processing your request")

async def verify_ton_transaction(tx_hash: str, expected_amount: float) -> bool:
    """Verify TON transaction"""
    try:
        # For testing, approve all transactions
        logger.warning("Skipping real transaction verification for testing")
        return True
        
        # Real implementation would verify against blockchain
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(
        #         f"https://tonapi.io/v1/blockchain/transactions/{tx_hash}",
        #         headers={"Authorization": f"Bearer {TON_API_KEY}"}
        #     )
        #     data = response.json()
        #     return data.get("success", False)
            
    except Exception as e:
        logger.error(f"Transaction verification error: {e}")
        return False

# ================= ADMIN FEATURES =================
async def admin_panel(update: Update, context: CallbackContext):
    """Show admin control panel"""
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Unauthorized")
        return
    
    keyboard = [
        [InlineKeyboardButton("Add Task", callback_data='admin_add_task')],
        [InlineKeyboardButton("Approve Payouts", callback_data='admin_approve_payouts')],
        [InlineKeyboardButton("Adjust Balances", callback_data='admin_adjust_balance')],
        [InlineKeyboardButton("View Statistics", callback_data='admin_stats')]
    ]
    
    await update.message.reply_text(
        "⚙️ Admin Panel",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_add_task(update: Update, context: CallbackContext):
    """Handle task creation"""
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ADMIN_IDS:
        await query.edit_message_text("❌ Unauthorized")
        return
    
    context.user_data['admin_action'] = 'add_task'
    await query.edit_message_text(
        "Send task details in this format:\n"
        "<code>Name|Description|Reward|VerificationType</code>\n\n"
        "Example:\n"
        "<code>Join Channel|Join our Telegram|5|telegram</code>",
        parse_mode='HTML'
    )

async def handle_admin_input(update: Update, context: CallbackContext):
    """Process admin commands"""
    if update.effective_user.id not in ADMIN_IDS:
        return
    
    action = context.user_data.get('admin_action')
    text = update.message.text
    
    if action == 'add_task':
        try:
            name, desc, reward, v_type = text.split('|')
            # Store task in bot_data
            context.bot_data.setdefault('tasks', {})
            task_id = f"task_{len(context.bot_data['tasks']) + 1}"
            context.bot_data['tasks'][task_id] = {
                'name': name.strip(),
                'desc': desc.strip(),
                'reward': float(reward),
                'verification': v_type.strip().lower()
            }
            
            await update.message.reply_text(
                f"✅ Task added successfully!\n\n"
                f"Name: {name.strip()}\n"
                f"Reward: {float(reward)} MINE\n"
                f"Type: {v_type.strip().lower()}"
            )
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)}")
        finally:
            context.user_data['admin_action'] = None

def setup_handlers(application):
    """Configure all bot handlers"""
    # User commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("connect", connect_wallet))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(admin_add_task, pattern='^admin_add_task$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_input))
    
    # Other handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_buttons))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_web_app_data))

def main():
    """Run the bot with proper error handling."""
    if not TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in .env file")
    
    try:
        # Create application with job queue
        application = (
            Application.builder()
            .token(TOKEN)
            .job_queue(JobQueue())
            .build()
        )
        
        # Initialize bot data
        application.bot_data['miners'] = {}
        application.bot_data['tasks'] = {}
        
        # Setup handlers
        setup_handlers(application)
        
        # Schedule daily task reset
        application.job_queue.run_daily(
            reset_daily_tasks,
            time=time(hour=0),
            days=tuple(range(7))
        )
        
        logger.info("Starting bot...")
        application.run_polling()
        
    except Conflict:
        logger.error("Another instance is already running. Exiting...")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()