import os
import json
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import telebot
from telebot.types import Message
import openai

# Load environment variables
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Initialize bot
bot = telebot.TeleBot(TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversation history directory
HISTORY_DIR = Path('conversation_history')
HISTORY_DIR.mkdir(exist_ok=True)

# User language preferences
user_languages = {}

# Russian language strings
RUSSIAN_STRINGS = {
    'start': '🤖 Привет! Я ChatGPT бот. Вот доступные команды:',
    'help': '📖 Справка по командам:',
    'commands': {
        '/start': 'Начать работу с ботом',
        '/help': 'Показать справку',
        '/russian': 'Переключиться на русский язык',
        '/english': 'Переключиться на английский язык',
        '/clear': 'Очистить историю диалога',
        '/history': 'Показать историю диалога',
        '/status': 'Показать статус бота',
    },
    'welcome': 'Добро пожаловать! Вы можете отправлять текстовые сообщения или файлы для анализа.',
    'language_set': 'Язык установлен на русский 🇷🇺',
    'english_set': 'Language set to English 🇬🇧',
    'history_cleared': 'История диалога очищена ✓',
    'no_history': 'История диалога пуста',
    'status': 'Статус бота: ✅ Онлайн',
    'processing': '⏳ Обработка вашего запроса...',
    'error': '❌ Произошла ошибка: {}',
    'file_received': '📄 Файл получен: {}',
    'file_analyzed': '✓ Файл проанализирован',
    'file_error': '❌ Ошибка при обработке файла: {}',
    'send_message': 'Отправьте сообщение для получения ответа от ChatGPT',
}

ENGLISH_STRINGS = {
    'start': '🤖 Hello! I am a ChatGPT bot. Here are the available commands:',
    'help': '📖 Command help:',
    'commands': {
        '/start': 'Start using the bot',
        '/help': 'Show help',
        '/russian': 'Switch to Russian language',
        '/english': 'Switch to English language',
        '/clear': 'Clear conversation history',
        '/history': 'Show conversation history',
        '/status': 'Show bot status',
    },
    'welcome': 'Welcome! You can send text messages or files for analysis.',
    'language_set': 'Language set to Russian 🇷🇺',
    'english_set': 'Language set to English 🇬🇧',
    'history_cleared': 'Conversation history cleared ✓',
    'no_history': 'Conversation history is empty',
    'status': 'Bot status: ✅ Online',
    'processing': '⏳ Processing your request...',
    'error': '❌ An error occurred: {}',
    'file_received': '📄 File received: {}',
    'file_analyzed': '✓ File analyzed',
    'file_error': '❌ Error processing file: {}',
    'send_message': 'Send a message to get a response from ChatGPT',
}


def get_user_language(user_id):
    """Get user's language preference (default: English)"""
    return user_languages.get(user_id, 'english')


def get_string(user_id, key):
    """Get localized string for user"""
    language = get_user_language(user_id)
    strings = RUSSIAN_STRINGS if language == 'russian' else ENGLISH_STRINGS
    return strings.get(key, key)


def get_history_file(user_id):
    """Get the path to user's conversation history file"""
    return HISTORY_DIR / f'user_{user_id}_history.json'


def load_conversation_history(user_id):
    """Load conversation history from JSON file"""
    history_file = get_history_file(user_id)
    if history_file.exists():
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f'Error loading history for user {user_id}: {e}')
            return []
    return []


def save_conversation_history(user_id, history):
    """Save conversation history to JSON file"""
    history_file = get_history_file(user_id)
    try:
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f'Error saving history for user {user_id}: {e}')


def add_to_history(user_id, role, content):
    """Add message to conversation history"""
    history = load_conversation_history(user_id)
    history.append({
        'role': role,
        'content': content,
        'timestamp': datetime.utcnow().isoformat()
    })
    save_conversation_history(user_id, history)
    return history


def get_gpt_response(user_id, user_message):
    """Get response from ChatGPT API"""
    try:
        # Load conversation history
        history = load_conversation_history(user_id)
        
        # Build messages for API
        messages = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in history
        ]
        
        # Add current user message
        messages.append({'role': 'user', 'content': user_message})
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=2000,
            temperature=0.7,
        )
        
        assistant_message = response['choices'][0]['message']['content']
        
        # Save both messages to history
        add_to_history(user_id, 'user', user_message)
        add_to_history(user_id, 'assistant', assistant_message)
        
        return assistant_message
    except Exception as e:
        logger.error(f'Error getting ChatGPT response: {e}')
        return None


def extract_text_from_file(file_path):
    """Extract text from uploaded file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            logger.error(f'Error reading file: {e}')
            return None
    except Exception as e:
        logger.error(f'Error extracting text: {e}')
        return None


@bot.message_handler(commands=['start'])
def handle_start(message: Message):
    """Handle /start command"""
    user_id = message.from_user.id
    user_languages[user_id] = 'english'  # Default to English
    
    help_text = get_string(user_id, 'start') + '\n\n'
    commands = get_string(user_id, 'commands')
    for cmd, desc in commands.items():
        help_text += f'{cmd} - {desc}\n'
    
    help_text += f'\n{get_string(user_id, "welcome")}'
    bot.reply_to(message, help_text)
    logger.info(f'User {user_id} started the bot')


@bot.message_handler(commands=['help'])
def handle_help(message: Message):
    """Handle /help command"""
    user_id = message.from_user.id
    
    help_text = get_string(user_id, 'help') + '\n\n'
    commands = get_string(user_id, 'commands')
    for cmd, desc in commands.items():
        help_text += f'{cmd} - {desc}\n'
    
    bot.reply_to(message, help_text)


@bot.message_handler(commands=['russian'])
def handle_russian(message: Message):
    """Switch to Russian language"""
    user_id = message.from_user.id
    user_languages[user_id] = 'russian'
    bot.reply_to(message, '🇷🇺 Язык установлен на русский')
    logger.info(f'User {user_id} switched to Russian')


@bot.message_handler(commands=['english'])
def handle_english(message: Message):
    """Switch to English language"""
    user_id = message.from_user.id
    user_languages[user_id] = 'english'
    bot.reply_to(message, '🇬🇧 Language set to English')
    logger.info(f'User {user_id} switched to English')


@bot.message_handler(commands=['clear'])
def handle_clear(message: Message):
    """Clear conversation history"""
    user_id = message.from_user.id
    history_file = get_history_file(user_id)
    
    if history_file.exists():
        try:
            history_file.unlink()
            bot.reply_to(message, get_string(user_id, 'history_cleared'))
            logger.info(f'User {user_id} cleared conversation history')
        except Exception as e:
            bot.reply_to(message, get_string(user_id, 'error').format(str(e)))
    else:
        bot.reply_to(message, get_string(user_id, 'no_history'))


@bot.message_handler(commands=['history'])
def handle_history(message: Message):
    """Show conversation history"""
    user_id = message.from_user.id
    history = load_conversation_history(user_id)
    
    if not history:
        bot.reply_to(message, get_string(user_id, 'no_history'))
        return
    
    history_text = '📜 История диалога:\n\n' if get_user_language(user_id) == 'russian' else '📜 Conversation History:\n\n'
    
    for i, msg in enumerate(history[-10:], 1):  # Show last 10 messages
        role = 'You' if msg['role'] == 'user' else 'Bot'
        timestamp = msg.get('timestamp', 'N/A')
        history_text += f'{i}. [{role}] {timestamp}\n{msg["content"][:100]}...\n\n'
    
    if len(history_text) > 4096:
        # Split message if too long
        bot.reply_to(message, history_text[:4096])
        bot.send_message(user_id, history_text[4096:])
    else:
        bot.reply_to(message, history_text)


@bot.message_handler(commands=['status'])
def handle_status(message: Message):
    """Show bot status"""
    user_id = message.from_user.id
    bot.reply_to(message, get_string(user_id, 'status'))


@bot.message_handler(content_types=['document'])
def handle_document(message: Message):
    """Handle document uploads"""
    user_id = message.from_user.id
    
    try:
        # Get file info
        file_info = bot.get_file(message.document.file_id)
        file_name = message.document.file_name
        
        # Download file
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temporarily
        temp_file_path = f'temp_{user_id}_{file_name}'
        with open(temp_file_path, 'wb') as f:
            f.write(downloaded_file)
        
        bot.reply_to(message, get_string(user_id, 'file_received').format(file_name))
        
        # Extract text
        file_content = extract_text_from_file(temp_file_path)
        
        if file_content:
            # Create analysis prompt
            analysis_prompt = f'Analyze the following text from file "{file_name}":\n\n{file_content[:2000]}'
            
            # Get ChatGPT response
            bot.send_message(user_id, get_string(user_id, 'processing'))
            response = get_gpt_response(user_id, analysis_prompt)
            
            if response:
                bot.send_message(user_id, response)
                bot.send_message(user_id, get_string(user_id, 'file_analyzed'))
                logger.info(f'User {user_id} uploaded and analyzed file: {file_name}')
            else:
                bot.send_message(user_id, get_string(user_id, 'error').format('Failed to get response'))
        else:
            bot.send_message(user_id, get_string(user_id, 'file_error').format('Unable to read file'))
        
        # Clean up temp file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            
    except Exception as e:
        logger.error(f'Error handling document: {e}')
        bot.reply_to(message, get_string(user_id, 'file_error').format(str(e)))


@bot.message_handler(func=lambda message: True)
def handle_message(message: Message):
    """Handle regular text messages"""
    user_id = message.from_user.id
    user_text = message.text
    
    # Show processing indicator
    processing_msg = bot.send_message(user_id, get_string(user_id, 'processing'))
    
    try:
        # Get response from ChatGPT
        response = get_gpt_response(user_id, user_text)
        
        if response:
            # Delete processing message
            bot.delete_message(user_id, processing_msg.message_id)
            # Send response
            bot.reply_to(message, response)
            logger.info(f'User {user_id} sent message and received response')
        else:
            bot.send_message(user_id, get_string(user_id, 'error').format('Failed to get response'))
    except Exception as e:
        logger.error(f'Error handling message: {e}')
        bot.send_message(user_id, get_string(user_id, 'error').format(str(e)))


def main():
    """Main bot loop"""
    logger.info('Bot started successfully')
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.error(f'Bot error: {e}')
        main()  # Restart on error


if __name__ == '__main__':
    main()
