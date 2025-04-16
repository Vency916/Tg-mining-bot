from telegram import Update
from telegram.ext import CallbackContext
from utils.database import get_user_data
from utils.chart_gen import generate_balance_chart
import config

def balance(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    user_data = get_user_data(user_id)
    
    # Generate chart
    chart_path = generate_balance_chart(user_id)
    
    # Format balance message
    balance_msg = (
        f"💰 Your Balance\n\n"
        f"Account: @{update.effective_user.username}\n"
        f"Unconfirmed Rewards: {user_data.get('unconfirmed', 0):.4f} MINE\n"
        f"Account Balance: {user_data.get('balance', 0):.4f} MINE\n"
        f"Next Payout ETA: In {config.PAYOUT_TIME} hours"
    )
    
    update.message.reply_photo(
        photo=open(chart_path, 'rb'),
        caption=balance_msg
    )