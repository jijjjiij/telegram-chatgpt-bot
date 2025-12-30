import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import g4f

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your Telegram bot token
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}! 👋\n\n"
        "I'm a ChatGPT bot powered by g4f. Send me any message and I'll respond using free ChatGPT API.\n\n"
        "Commands:\n"
        "/start - Show this welcome message\n"
        "/help - Show help information\n"
        "/clear - Clear conversation history"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "🤖 ChatGPT Telegram Bot\n\n"
        "This bot uses g4f library to provide free access to ChatGPT.\n\n"
        "How to use:\n"
        "1. Just send any message and I'll respond with ChatGPT's reply\n"
        "2. Use /clear to reset our conversation\n"
        "3. Use /start to see the welcome message\n\n"
        "⚠️ Note: Responses may take a moment to generate."
    )
    await update.message.reply_text(help_text)


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the conversation history for the user."""
    context.user_data.clear()
    await update.message.reply_text("✅ Conversation history cleared!")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and generate responses using g4f."""
    user_message = update.message.text
    user_id = update.effective_user.id
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    try:
        # Get conversation history from user data
        if "history" not in context.user_data:
            context.user_data["history"] = []
        
        history = context.user_data["history"]
        
        # Add user message to history
        history.append({
            "role": "user",
            "content": user_message
        })
        
        # Generate response using g4f
        logger.info(f"Generating response for user {user_id}")
        
        response = await g4f.ChatCompletion.create_async(
            model=g4f.models.default,
            messages=history,
            timeout=60,
        )
        
        bot_response = str(response).strip()
        
        # Add bot response to history
        history.append({
            "role": "assistant",
            "content": bot_response
        })
        
        # Keep only last 10 messages in history to avoid memory issues
        if len(history) > 20:
            context.user_data["history"] = history[-20:]
        
        # Send response in chunks if it's too long (Telegram has a 4096 character limit)
        if len(bot_response) > 4096:
            for i in range(0, len(bot_response), 4096):
                await update.message.reply_text(bot_response[i:i+4096])
        else:
            await update.message.reply_text(bot_response)
            
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        await update.message.reply_text(
            "❌ Sorry, I encountered an error while processing your request. "
            "Please try again later or use /clear to reset the conversation."
        )


def main() -> None:
    """Start the bot."""
    # Create the Application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("clear", clear_command))
    
    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run the bot
    logger.info("Starting Telegram ChatGPT Bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
