"""
Telegram ChatGPT Bot using aiogram framework with Russian language support
Features:
- aiogram 3.x framework
- Russian language support
- g4f integration for free ChatGPT access
- Conversation history persistence
- File handling (images, documents)
"""

import logging
import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List
import aiofiles

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, File, Document
from aiogram.utils.markdown import hbold, hcode

try:
    import g4f
except ImportError:
    g4f = None

# Configuration
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
HISTORY_DIR = Path('conversation_history')
UPLOADS_DIR = Path('uploads')
MAX_HISTORY_MESSAGES = 20
LOG_LEVEL = logging.INFO

# Create necessary directories
HISTORY_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Russian language strings
TEXTS = {
    'welcome': '👋 Добро пожаловать в ChatGPT бот!\n\nДоступные команды:\n/start - Начать\n/clear - Очистить историю\n/help - Справка\n/status - Статус бота',
    'help': '''ℹ️ Справка:
• Просто отправьте сообщение для чата
• /clear - очистить историю разговора
• /history - показать историю
• /status - информация о боте
• Отправляйте фото и документы для обработки
''',
    'cleared': '✅ История разговора очищена',
    'processing': '⏳ Обрабатываю ваш запрос...',
    'error': '❌ Ошибка: {error}',
    'no_history': '📭 История пуста',
    'history_header': '📋 История разговора:\n\n',
    'status': '''📊 Статус бота:
Версия: 1.0
Фреймворк: aiogram 3.x
Модель: g4f (ChatGPT)
Язык: Русский
Статус: ✅ Онлайн''',
    'file_saved': '💾 Файл сохранён: {filename}',
    'file_error': '❌ Ошибка при сохранении файла: {error}',
    'typing': '✍️ {name} печатает...',
}


# FSM States
class BotStates(StatesGroup):
    waiting_for_message = State()
    processing = State()


class ConversationHistory:
    """Manager for conversation history persistence"""
    
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.history_file = HISTORY_DIR / f'{user_id}.json'
        self.messages: List[Dict] = []
        self._load_history()
    
    def _load_history(self):
        """Load conversation history from file"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.messages = data.get('messages', [])
                logger.info(f'Loaded {len(self.messages)} messages for user {self.user_id}')
        except Exception as e:
            logger.error(f'Error loading history: {e}')
            self.messages = []
    
    async def _save_history(self):
        """Save conversation history to file"""
        try:
            async with aiofiles.open(self.history_file, 'w', encoding='utf-8') as f:
                data = {
                    'user_id': self.user_id,
                    'messages': self.messages,
                    'last_update': datetime.now().isoformat()
                }
                await f.write(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f'Error saving history: {e}')
    
    def add_message(self, role: str, content: str):
        """Add message to history"""
        self.messages.append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last MAX_HISTORY_MESSAGES
        if len(self.messages) > MAX_HISTORY_MESSAGES:
            self.messages = self.messages[-MAX_HISTORY_MESSAGES:]
    
    async def save(self):
        """Save history asynchronously"""
        await self._save_history()
    
    def clear(self):
        """Clear conversation history"""
        self.messages = []
    
    def get_context(self) -> List[Dict]:
        """Get conversation context for AI"""
        return [{'role': msg['role'], 'content': msg['content']} 
                for msg in self.messages]
    
    def get_display(self) -> str:
        """Get formatted history for display"""
        if not self.messages:
            return TEXTS['no_history']
        
        display = TEXTS['history_header']
        for msg in self.messages[-10:]:  # Show last 10 messages
            role = '👤 Вы' if msg['role'] == 'user' else '🤖 Бот'
            content = msg['content'][:100] + '...' if len(msg['content']) > 100 else msg['content']
            display += f'{role}: {content}\n'
        return display


class FileHandler:
    """Handle file uploads and processing"""
    
    @staticmethod
    async def save_file(bot: Bot, file_id: str, file_name: str) -> Optional[str]:
        """Download and save file from Telegram"""
        try:
            file = await bot.get_file(file_id)
            file_path = UPLOADS_DIR / file_name
            
            await bot.download_file(file.file_path, str(file_path))
            logger.info(f'File saved: {file_path}')
            return str(file_path)
        except Exception as e:
            logger.error(f'Error saving file: {e}')
            return None
    
    @staticmethod
    def get_file_description(file_path: str) -> str:
        """Get description of file content"""
        try:
            path = Path(file_path)
            size = path.stat().st_size
            size_mb = size / (1024 * 1024)
            return f'Файл: {path.name} ({size_mb:.2f} MB)'
        except Exception as e:
            return f'Ошибка при чтении файла: {e}'


class ChatGPTClient:
    """Client for interacting with ChatGPT via g4f"""
    
    def __init__(self):
        self.provider = None
        self._init_provider()
    
    def _init_provider(self):
        """Initialize g4f provider"""
        if g4f is None:
            logger.warning('g4f is not installed. Install it with: pip install g4f')
            return
        
        try:
            self.provider = g4f.Provider.Bing
            logger.info(f'Initialized provider: {self.provider}')
        except Exception as e:
            logger.error(f'Error initializing provider: {e}')
    
    async def get_response(self, messages: List[Dict], user_name: str = 'Пользователь') -> Optional[str]:
        """Get response from ChatGPT"""
        if self.provider is None:
            return '⚠️ g4f не настроен. Установите: pip install g4f'
        
        try:
            logger.info(f'Requesting response for {len(messages)} messages')
            
            # Run g4f in thread pool to avoid blocking
            response = await asyncio.to_thread(
                self._make_request,
                messages
            )
            return response
        except Exception as e:
            logger.error(f'Error getting response: {e}')
            return TEXTS['error'].format(error=str(e)[:100])
    
    def _make_request(self, messages: List[Dict]) -> str:
        """Make synchronous request to g4f"""
        try:
            response = g4f.ChatCompletion.create(
                model=g4f.models.gpt_4,
                messages=messages,
                stream=False,
            )
            return str(response) if response else '❌ Пустой ответ от модели'
        except Exception as e:
            raise e


# Global objects
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
chatgpt = ChatGPTClient()
conversations: Dict[int, ConversationHistory] = {}


def get_conversation(user_id: int) -> ConversationHistory:
    """Get or create conversation history for user"""
    if user_id not in conversations:
        conversations[user_id] = ConversationHistory(user_id)
    return conversations[user_id]


# Handlers
@dp.message(Command('start'))
async def cmd_start(message: Message, state: FSMContext):
    """Start command handler"""
    logger.info(f'User {message.from_user.id} started the bot')
    await message.answer(TEXTS['welcome'])
    await state.set_state(BotStates.waiting_for_message)


@dp.message(Command('help'))
async def cmd_help(message: Message):
    """Help command handler"""
    await message.answer(TEXTS['help'])


@dp.message(Command('clear'))
async def cmd_clear(message: Message):
    """Clear conversation history"""
    conv = get_conversation(message.from_user.id)
    conv.clear()
    await conv.save()
    await message.answer(TEXTS['cleared'])


@dp.message(Command('history'))
async def cmd_history(message: Message):
    """Show conversation history"""
    conv = get_conversation(message.from_user.id)
    history_text = conv.get_display()
    
    # Split long messages
    if len(history_text) > 4096:
        parts = [history_text[i:i+4096] for i in range(0, len(history_text), 4096)]
        for part in parts:
            await message.answer(part)
    else:
        await message.answer(history_text)


@dp.message(Command('status'))
async def cmd_status(message: Message):
    """Show bot status"""
    await message.answer(TEXTS['status'])


@dp.message(F.photo)
async def handle_photo(message: Message):
    """Handle photo uploads"""
    try:
        photo = message.photo[-1]  # Get highest quality
        file_info = await bot.get_file(photo.file_id)
        
        filename = f'photo_{message.from_user.id}_{datetime.now().timestamp()}.jpg'
        file_path = await FileHandler.save_file(bot, photo.file_id, filename)
        
        if file_path:
            conv = get_conversation(message.from_user.id)
            description = FileHandler.get_file_description(file_path)
            conv.add_message('user', f'📷 {description}')
            
            await message.answer(TEXTS['file_saved'].format(filename=filename))
            await message.answer(f'✅ {description}')
            await conv.save()
        else:
            await message.answer(TEXTS['file_error'].format(error='Не удалось загрузить'))
    except Exception as e:
        logger.error(f'Error handling photo: {e}')
        await message.answer(TEXTS['file_error'].format(error=str(e)[:50]))


@dp.message(F.document)
async def handle_document(message: Message):
    """Handle document uploads"""
    try:
        document = message.document
        filename = f'{message.from_user.id}_{datetime.now().timestamp()}_{document.file_name}'
        
        file_path = await FileHandler.save_file(bot, document.file_id, filename)
        
        if file_path:
            conv = get_conversation(message.from_user.id)
            description = FileHandler.get_file_description(file_path)
            conv.add_message('user', f'📄 {description}')
            
            await message.answer(TEXTS['file_saved'].format(filename=document.file_name))
            await conv.save()
        else:
            await message.answer(TEXTS['file_error'].format(error='Не удалось загрузить'))
    except Exception as e:
        logger.error(f'Error handling document: {e}')
        await message.answer(TEXTS['file_error'].format(error=str(e)[:50]))


@dp.message(StateFilter(None) | BotStates.waiting_for_message)
async def handle_message(message: Message, state: FSMContext):
    """Main message handler for chat"""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name or 'Пользователь'
        
        # Show typing indicator
        async with bot.context_manager.get_chat_member(message.chat.id, user_id):
            await message.chat.send_action('typing')
        
        # Show processing message
        status_msg = await message.answer(TEXTS['processing'])
        
        # Get conversation history
        conv = get_conversation(user_id)
        
        # Add user message to history
        conv.add_message('user', message.text)
        
        # Get conversation context
        context = conv.get_context()
        
        logger.info(f'User {user_id} ({user_name}): {message.text}')
        
        # Get response from ChatGPT
        await state.set_state(BotStates.processing)
        response = await chatgpt.get_response(context, user_name)
        
        # Add assistant response to history
        if response and response.startswith('❌') is False:
            conv.add_message('assistant', response)
        
        # Save conversation history
        await conv.save()
        
        # Send response
        if response:
            if len(response) > 4096:
                # Split long messages
                parts = [response[i:i+4096] for i in range(0, len(response), 4096)]
                await status_msg.delete()
                for part in parts:
                    await message.answer(part)
            else:
                await status_msg.edit_text(response)
        else:
            await status_msg.edit_text('❌ Не удалось получить ответ')
        
        await state.set_state(BotStates.waiting_for_message)
        
    except Exception as e:
        logger.error(f'Error in message handler: {e}')
        await message.answer(TEXTS['error'].format(error=str(e)[:100]))
        await state.set_state(BotStates.waiting_for_message)


async def main():
    """Main function to start the bot"""
    logger.info('Starting Telegram ChatGPT Bot...')
    logger.info(f'Bot Token: {TOKEN[:10]}...')
    logger.info(f'g4f available: {g4f is not None}')
    
    try:
        # Start polling
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types()
        )
    except Exception as e:
        logger.error(f'Error in main: {e}')
    finally:
        await bot.session.close()


if __name__ == '__main__':
    asyncio.run(main())
