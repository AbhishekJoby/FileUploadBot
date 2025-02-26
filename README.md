# tg_upload_bot

## Setup

1. Clone the repository
2. Create a `.env` file based on `.env.example`
3. Fill in your environment variables:
   - Get `TELEGRAM_BOT_TOKEN` from @BotFather
   - Get `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` from my.telegram.org
   - Set `LOCAL_API_SERVER` for your local Telegram API server
   - Set `PARENT_FOLDER_ID` for Google Drive uploads

4. Install dependencies:
   - `pip install -r requirements.txt`

5. Run the Server in local mode:
   - `./telegram-bot-api/bin/telegram-bot-api --api-id=$TELEGRAM_API_ID --api-hash=$TELEGRAM_API_HASH --local`

5. Run the bot:
   - `python bot.py`
