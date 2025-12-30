# Telegram ChatGPT Bot

A Telegram bot that leverages OpenAI's ChatGPT API to provide intelligent conversational responses.

## Features

- 🤖 AI-powered responses using ChatGPT
- 💬 Seamless Telegram integration
- ⚡ Fast and responsive interactions
- 🔒 Secure API key management
- 📝 Conversation history support

## Prerequisites

Before setting up the bot, ensure you have:

- Python 3.8 or higher
- A Telegram account
- OpenAI API key (get one from [OpenAI Platform](https://platform.openai.com/api-keys))
- Telegram Bot Token (create one using [@BotFather](https://t.me/botfather) on Telegram)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/jijjjiij/telegram-chatgpt-bot.git
cd telegram-chatgpt-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

Edit the `.env` file and add your credentials:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
OPENAI_API_KEY=your_openai_api_key_here
```

**Important:** Never commit the `.env` file to version control. It contains sensitive information.

### 5. Run the Bot

```bash
python main.py
```

You should see a message indicating the bot is running and polling for messages.

## Usage

### Starting the Bot

1. Search for your bot on Telegram using the username you created with [@BotFather](https://t.me/botfather)
2. Click the "Start" button or send the `/start` command
3. Begin sending messages to chat with ChatGPT

### Commands

- `/start` - Initialize the bot and see welcome message
- `/help` - Display available commands
- `/reset` - Clear conversation history
- `/about` - Show bot information

### Example Interactions

```
You: Hello, how are you?
Bot: I'm doing great, thank you for asking! How can I help you today?

You: What's the capital of France?
Bot: The capital of France is Paris. It's known for its art, culture, and iconic landmarks like the Eiffel Tower.
```

## Configuration

### Advanced Settings

You can customize the bot behavior by modifying the configuration variables:

- **Model**: Change the ChatGPT model (default: `gpt-3.5-turbo`)
- **Temperature**: Control response randomness (0-2, lower = more deterministic)
- **Max Tokens**: Limit response length

Edit these settings in the configuration file or environment variables as needed.

## File Structure

```
telegram-chatgpt-bot/
├── main.py              # Main bot application
├── config.py            # Configuration settings
├── handlers/            # Message and command handlers
├── utils/               # Utility functions
├── requirements.txt     # Python dependencies
├── .env.example         # Example environment variables
└── README.md            # This file
```

## Troubleshooting

### Bot Not Responding

1. Verify your Telegram Bot Token is correct
2. Check your internet connection
3. Ensure the bot script is still running
4. Check the console logs for error messages

### OpenAI API Errors

1. Verify your OpenAI API key is valid
2. Check your OpenAI account has available credits
3. Ensure you're not exceeding rate limits
4. Review the error message in the console

### Connection Issues

1. Check your firewall settings
2. Ensure your internet connection is stable
3. Verify Telegram's API endpoint is accessible from your location

## Security Considerations

- 🔐 Keep your `.env` file and API keys confidential
- 🚫 Don't share your bot token publicly
- 🔄 Rotate your API keys periodically
- 📊 Monitor your API usage to avoid unexpected charges

## Performance Tips

- Use a more efficient model variant if speed is critical
- Adjust temperature and max tokens based on your use case
- Consider implementing caching for frequently asked questions
- Monitor API usage and costs regularly

## Contributing

Contributions are welcome! Please feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues, questions, or suggestions:

1. Check the [Issues](https://github.com/jijjjiij/telegram-chatgpt-bot/issues) page
2. Create a new issue with detailed information
3. Include error logs and steps to reproduce

## Disclaimer

This bot is not affiliated with OpenAI or Telegram. Usage of this bot is subject to:

- [Telegram's Terms of Service](https://telegram.org/tos)
- [OpenAI's Terms of Service](https://openai.com/terms)

Please use responsibly and in accordance with all applicable terms of service.

## Acknowledgments

- [OpenAI](https://openai.com/) for the ChatGPT API
- [python-telegram-bot](https://python-telegram-bot.readthedocs.io/) library
- The open-source community

---

**Last Updated:** 2025-12-30

For the latest updates and releases, visit the [GitHub repository](https://github.com/jijjjiij/telegram-chatgpt-bot).
