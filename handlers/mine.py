from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext, MessageHandler, filters
from utils.database import get_user_data, update_mining_stats
from utils.chart_gen import generate_mining_chart
import config
import asyncio

active_miners = set()

async def mine_command(update: Update, context: CallbackContext):
    """Show mining dashboard"""
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    chart_path = await asyncio.to_thread(generate_mining_chart, user_id)
    
    status = "⛏️ ACTIVE" if user_id in active_miners else "⏸️ INACTIVE"
    keyboard = [
        ["▶ Start Mining", "⏹ Stop Mining"],
        ["📊 Statistics", "🏠 Main Menu"]
    ]
    
    await update.message.reply_photo(
        photo=chart_path,
        caption=f"""
🔧 Mining Dashboard
━━━━━━━━━━━━━━
Status: {status}
Hash Rate: {user_data['hash_rate']:.1f} MH/s
Unconfirmed: {user_data['unconfirmed']:.6f} MINE
Balance: {user_data['balance']:.6f} MINE
━━━━━━━━━━━━━━
Next payout in {config.PAYOUT_INTERVAL} hours
        """,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def start_mining(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in active_miners:
        active_miners.add(user_id)
        asyncio.create_task(mining_process(update, context))
        await update.message.reply_text("⛏ Mining started successfully!")
    else:
        await update.message.reply_text("⚠️ You're already mining!")

async def stop_mining(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id in active_miners:
        active_miners.remove(user_id)
        await update.message.reply_text("⏸ Mining stopped!")
    else:
        await update.message.reply_text("⚠️ No active mining session!")

async def mining_process(update: Update, context: CallbackContext):
    """Background mining task"""
    user_id = update.effective_user.id
    
    while user_id in active_miners:
        user_data = get_user_data(user_id)
        mined = config.MINING_RATE * user_data['hash_rate']
        update_mining_stats(user_id, mined)
        await asyncio.sleep(1)

def get_handlers():
    return [
        MessageHandler(filters.Regex(r'^▶ Start Mining$'), start_mining),
        MessageHandler(filters.Regex(r'^⏹ Stop Mining$'), stop_mining),
        CommandHandler('mine', mine_command)
    ]