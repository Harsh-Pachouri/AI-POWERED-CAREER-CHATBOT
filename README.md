# Career Resources Telegram Bot

A Telegram bot to store, search, and manage career-related resources using AWS DynamoDB and semantic search with FAISS and Sentence Transformers.

## Features
- Store resource links and descriptions
- Semantic and keyword search for resources
- Delete individual or all resources
- AWS DynamoDB backend
- FAISS-based semantic search

## Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/your-repo.git
   cd your-repo
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Set environment variables:**
   - `TELEGRAM_BOT_TOKEN`: Your Telegram bot token
   - AWS credentials: Set up via environment variables or AWS config/credentials files

   You can use a `.env` file (add `.env` to `.gitignore`):
   ```env
   TELEGRAM_BOT_TOKEN=your-telegram-bot-token
   AWS_ACCESS_KEY_ID=your-access-key
   AWS_SECRET_ACCESS_KEY=your-secret-key
   AWS_DEFAULT_REGION=your-region
   ```

## Usage
Run the bot:
```bash
python bot.py
```

### Telegram Commands
- `/start` — Show help message
- `/store <link> <description>` — Store a resource
- `/search <keyword>` — Search for resources
- `/delete <link>` — Delete the last searched resource
- `/delete_all` — Delete all resources

## Notes
- Make sure your AWS DynamoDB table is set up and accessible.
- Do **not** commit your credentials or `.env` file.

## License
[MIT](LICENSE)
