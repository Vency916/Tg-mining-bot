from telegram import ReplyKeyboardMarkup
from telegram.ext import ConversationHandler

def start(update, context):
    user = update.effective_user
    keyboard = [
        ['Farm', 'Mining'],
        ['Payment', 'Settings'],
        ['Statistics', 'Tools']
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    update.message.reply_text(
        f"Welcome {user.first_name} to SMINE Bot!\n\n"
        "Use the buttons below to navigate:",
        reply_markup=reply_markup
    )