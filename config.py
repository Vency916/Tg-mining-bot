# Add at the top with other imports
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def main():
    # Get token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No token found. Create .env file with TELEGRAM_BOT_TOKEN")
    
    # Create application
    application = Application.builder().token(token).build()
    # ... rest of your code
ADMIN_IDS = [6712967629]  # Replace with your numeric chat ID