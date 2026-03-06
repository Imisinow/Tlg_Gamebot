import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Replace with your token from @BotFather
TOKEN = "YOUR_BOT_TOKEN"
# Replace with your GitHub Pages link (where you hosted the HTML)
MINI_APP_URL = "https://yourusername.github.io/spinning-game/"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # This captures the referral ID from the link
    
    referrer_id = args[0] if args else None
    
    # If there's a referrer, we notify the backend
    if referrer_id:
        import requests
        # Tell your Python API (the one on your VPS/Render) about the new referral
        try:
            requests.post(f"http://YOUR_VPS_IP:8000/register_referral?user_id={user.id}&referrer_id={referrer_id}")
        except:
            pass

    # The Button that opens the game
    keyboard = [
        [InlineKeyboardButton("🎰 Play & Earn TON", web_app=WebAppInfo(url=MINI_APP_URL))]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Hi {user.first_name}! 👋\n\nReady to spin and win? Click the button below to start!",
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("Bot is running...")
    app.run_polling()
