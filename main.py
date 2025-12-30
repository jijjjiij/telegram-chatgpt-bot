#!/usr/bin/env python3
"""
Telegram ChatGPT Bot with g4f Integration
Features:
- g4f library integration instead of OpenAI API
- Russian language support
- Conversation history persistence
- File handling capabilities
"""

import logging
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

from telegram import Update, Document
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from telegram.constants import ChatAction

try:
    import g4f
except ImportError:
    print("Please install g4f: pip install g4f")
    exit(1)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
CONVERSATION_DIR = Path("conversations")
MAX_HISTORY_LENGTH = 50
SUPPORTED_FILE_TYPES = {'.txt', '.md', '.pdf', '.json', '.py', '.js', '.html', '.css'}
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Russian translations
TRANSLATIONS = {
    'en': {
        'welcome': 'Welcome! I\'m a ChatGPT-powered bot using g4f. Send me any message and I\'ll respond.',
        'help': (
            'Available commands:\n'
            '/start - Start the bot\n'
            '/help - Show this message\n'
            '/clear - Clear conversation history\n'
            '/history - Show conversation history\n'
            '/language - Switch language (en/ru)\n'
            '/file - Send a file for analysis\n\n'
            'Just send me any message to chat!'
        ),
        'cleared': '✓ Conversation history cleared.',
        'history_empty': 'No conversation history yet.',
        'typing': 'Typing...',
        'error': 'Sorry, an error occurred. Please try again.',
        'language_switched': 'Language switched to English.',
        'file_received': 'File received: {}. Processing...',
        'file_error': 'Error processing file: {}',
        'unsupported_file': 'Unsupported file type. Supported: {}',
        'no_file': 'Please attach a file to analyze.',
    },
    'ru': {
        'welcome': 'Добро пожаловать! Я чат-бот на основе ChatGPT с использованием g4f. Отправьте мне любое сообщение, и я отвечу.',
        'help': (
            'Доступные команды:\n'
            '/start - Запустить бота\n'
            '/help - Показать эту справку\n'
            '/clear - Очистить историю разговора\n'
            '/history - Показать историю разговора\n'
            '/language - Переключить язык (en/ru)\n'
            '/file - Отправить файл для анализа\n\n'
            'Просто отправьте мне любое сообщение для общения!'
        ),
        'cleared': '✓ История разговора очищена.',
        'history_empty': 'История разговора пуста.',
        'typing': 'Печатаю...',
        'error': 'Извините, произошла ошибка. Пожалуйста, попробуйте ��нова.',
        'language_switched': 'Язык переключен на русский.',
        'file_received': 'Файл получен: {}. Обработка...',
        'file_error': 'Ошибка при обработке файла: {}',
        'unsupported_file': 'Неподдерживаемый тип файла. Поддерживаемые: {}',
        'no_file': 'Пожалуйста, приложите файл для анализа.',
    }
}


class ConversationManager:
    """Manages conversation history persistence"""

    def __init__(self, user_id: int, language: str = 'en'):
        self.user_id = user_id
        self.language = language
        self.history_file = CONVERSATION_DIR / f"user_{user_id}.json"
        self.conversation: List[Dict[str, str]] = []
        self._load_history()

    def _ensure_dir(self):
        """Ensure conversation directory exists"""
        CONVERSATION_DIR.mkdir(exist_ok=True)

    def _load_history(self):
        """Load conversation history from file"""
        self._ensure_dir()
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.conversation = data.get('conversation', [])
                    self.language = data.get('language', 'en')
            except Exception as e:
                logger.error(f"Error loading history: {e}")
                self.conversation = []

    def save_history(self):
        """Save conversation history to file"""
        self._ensure_dir()
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'user_id': self.user_id,
                    'language': self.language,
                    'conversation': self.conversation,
                    'timestamp': datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving history: {e}")

    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.conversation.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })

        # Keep history within limit
        if len(self.conversation) > MAX_HISTORY_LENGTH:
            self.conversation = self.conversation[-MAX_HISTORY_LENGTH:]

        self.save_history()

    def get_history(self, limit: int = None) -> List[Dict[str, str]]:
        """Get conversation history"""
        if limit:
            return self.conversation[-limit:]
        return self.conversation

    def clear_history(self):
        """Clear conversation history"""
        self.conversation = []
        self.save_history()

    def set_language(self, language: str):
        """Set user language"""
        if language in TRANSLATIONS:
            self.language = language
            self.save_history()
            return True
        return False


class G4FBot:
    """Main bot class using g4f integration"""

    def __init__(self, bot_token: str):
        self.application = Application.builder().token(bot_token).build()
        self.setup_handlers()
        self.conversation_managers: Dict[int, ConversationManager] = {}

    def get_manager(self, user_id: int) -> ConversationManager:
        """Get or create conversation manager for user"""
        if user_id not in self.conversation_managers:
            self.conversation_managers[user_id] = ConversationManager(user_id)
        return self.conversation_managers[user_id]

    def get_translation(self, user_id: int, key: str) -> str:
        """Get translation for user's language"""
        manager = self.get_manager(user_id)
        lang = manager.language
        return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, TRANSLATIONS['en'].get(key, ''))

    def setup_handlers(self):
        """Setup command and message handlers"""
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("clear", self.clear_history))
        self.application.add_handler(CommandHandler("history", self.show_history))
        self.application.add_handler(CommandHandler("language", self.language_command))
        self.application.add_handler(CommandHandler("file", self.file_command))

        self.application.add_handler(
            MessageHandler(filters.Document.ALL, self.handle_file)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message)
        )

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start command handler"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)
        welcome_msg = self.get_translation(user_id, 'welcome')

        await update.message.reply_text(welcome_msg)
        logger.info(f"User {user_id} started the bot")

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Help command handler"""
        user_id = update.effective_user.id
        help_msg = self.get_translation(user_id, 'help')
        await update.message.reply_text(help_msg)

    async def clear_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Clear conversation history"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)
        manager.clear_history()

        cleared_msg = self.get_translation(user_id, 'cleared')
        await update.message.reply_text(cleared_msg)
        logger.info(f"User {user_id} cleared conversation history")

    async def show_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show conversation history"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)
        history = manager.get_history()

        if not history:
            empty_msg = self.get_translation(user_id, 'history_empty')
            await update.message.reply_text(empty_msg)
            return

        history_text = "📋 Conversation History:\n\n"
        for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
            role = "👤" if msg['role'] == 'user' else "🤖"
            timestamp = msg.get('timestamp', '')[:16]
            history_text += f"{i}. {role} [{timestamp}]\n{msg['content']}\n\n"

        await update.message.reply_text(history_text, parse_mode=None)

    async def language_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle language switching"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)

        if context.args and context.args[0] in ['en', 'ru']:
            language = context.args[0]
            if manager.set_language(language):
                lang_msg = self.get_translation(user_id, 'language_switched')
                await update.message.reply_text(lang_msg)
                logger.info(f"User {user_id} switched to {language}")
        else:
            await update.message.reply_text("Use /language en or /language ru")

    async def file_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Inform user how to send files"""
        user_id = update.effective_user.id
        msg = self.get_translation(user_id, 'no_file')
        await update.message.reply_text(msg)

    async def handle_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle file uploads and analysis"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)
        document = update.message.document

        # Check file type
        file_ext = Path(document.file_name).suffix.lower()
        if file_ext not in SUPPORTED_FILE_TYPES:
            error_msg = self.get_translation(user_id, 'unsupported_file')
            supported = ', '.join(SUPPORTED_FILE_TYPES)
            await update.message.reply_text(error_msg.format(supported))
            return

        try:
            # Download and read file
            file = await context.bot.get_file(document.file_id)
            file_path = f"temp_{user_id}_{document.file_name}"

            await file.download_to_drive(file_path)

            with open(file_path, 'r', encoding='utf-8') as f:
                file_content = f.read()

            # Clean up temp file
            os.remove(file_path)

            # Create analysis prompt
            received_msg = self.get_translation(user_id, 'file_received')
            await update.message.reply_text(received_msg.format(document.file_name))

            analysis_prompt = (
                f"Please analyze the following file content ({document.file_name}):\n\n"
                f"{file_content[:2000]}"  # Limit content length
            )

            # Get AI response
            response = await self.get_ai_response(analysis_prompt, manager)
            manager.add_message('user', f'[File Analysis] {document.file_name}')
            manager.add_message('assistant', response)

            await update.message.reply_text(response)

        except Exception as e:
            error_msg = self.get_translation(user_id, 'file_error')
            await update.message.reply_text(error_msg.format(str(e)))
            logger.error(f"Error handling file: {e}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user_id = update.effective_user.id
        manager = self.get_manager(user_id)
        user_message = update.message.text

        # Show typing indicator
        await update.message.chat.send_action(ChatAction.TYPING)

        # Add user message to history
        manager.add_message('user', user_message)

        try:
            # Get AI response
            response = await self.get_ai_response(user_message, manager)

            # Add assistant message to history
            manager.add_message('assistant', response)

            # Send response
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            error_msg = self.get_translation(user_id, 'error')
            await update.message.reply_text(error_msg)

    async def get_ai_response(self, user_input: str, manager: ConversationManager) -> str:
        """Get response from g4f"""
        try:
            # Prepare conversation history for g4f
            messages = [
                {"role": msg['role'], "content": msg['content']}
                for msg in manager.get_history()[-10:]  # Use last 10 messages for context
            ]

            # Add current user message if not already in history
            if not messages or messages[-1]['content'] != user_input:
                messages.append({"role": "user", "content": user_input})

            # Get response from g4f
            response = await asyncio.to_thread(
                self._call_g4f,
                messages,
                manager.language
            )

            return response if response else self.get_translation(
                manager.user_id, 'error'
            )

        except Exception as e:
            logger.error(f"Error getting AI response: {e}")
            raise

    @staticmethod
    def _call_g4f(messages: List[Dict[str, str]], language: str) -> str:
        """Call g4f API synchronously"""
        try:
            # Add system prompt with language preference
            system_prompt = (
                f"You are a helpful assistant. Respond in {language} language. "
                "Be concise and helpful."
            )

            full_messages = [
                {"role": "system", "content": system_prompt},
                *messages
            ]

            # Try to get response from g4f
            response = g4f.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=full_messages,
            )

            if isinstance(response, str):
                return response
            else:
                # Handle generator/iterator response
                return "".join(response) if response else "No response"

        except Exception as e:
            logger.error(f"g4f error: {e}")
            raise

    def run(self):
        """Run the bot"""
        logger.info("Starting Telegram ChatGPT Bot with g4f...")
        self.application.run_polling()


def main():
    """Main entry point"""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("Please set TELEGRAM_BOT_TOKEN environment variable")
        return

    bot = G4FBot(BOT_TOKEN)
    bot.run()


if __name__ == "__main__":
    main()
