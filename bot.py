import os
import shutil
import platform
import asyncio
from typing import final
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
from pathlib import Path

# Get the parent directory of the current file
#parent_dir = Path(__file__).parent.parent.parent

#mode
localMode = True

# PRIVATE VARIABLES
load_dotenv()
# Add Local API configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

PARENT_FOLDER_ID = os.getenv('PARENT_FOLDER_ID')

SERVICE_ACCOUNT_FILE = 'service_acc.json'
SCOPES = ['https://www.googleapis.com/auth/drive.file']
UPLOAD_INTERVAL = 1  # Update progress every 3 seconds


# Google Drive API setup
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Welcome to the bot.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('This bot is under development. Stay tuned for updates.')

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bot is shutting down...')
    await stop_bot(context.application)

# Text message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    enquiry: str = update.message.text
    bot_reply_txt: str = 'I dont understand your message.'

    if update.message.chat.type == 'group':
        bot_reply_txt = 'This bot is currently not compatible with group chats.'
    elif enquiry.lower() == 'hai':
        bot_reply_txt = 'Hello!'
    elif enquiry.lower() == 'da':
        bot_reply_txt = 'ennada!'

    await update.message.reply_text(bot_reply_txt)

# Document handler
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file_id: str = update.message.document.file_id
    file_name: str = update.message.document.file_name
    
    print("recieved file: ",file_name )
    
    file = await context.bot.get_file(file_id)
    #os.makedirs(os.path.dirname("downloads"), exist_ok=True)


    if(localMode==False):

        # Download the file from Telegram
        file_path = f'downloads/{file_name}'
        print("downloading file from telegram")
        await file.download_to_drive(custom_path=file_path,read_timeout=10)
        
        print("file downloaded")
        await asyncio.sleep(1)
      # Small delay to ensure file operations are completed
    else:
        
        
        
        linux_path  = file.file_path.replace(f"https://api.telegram.org/file/bot{BOT_TOKEN}//","")
        print("the system is",platform.system())
        if(platform.system()=="Windows"):

            print("does not work on windows")
            #does not work on windows
            print("changing path")
            print(linux_path[4])
            driveLetter = linux_path[4]
            windows_path = linux_path.replace(f"mnt/{driveLetter}/", f"{driveLetter.upper()}:\\").replace("/", r"\\")
            
            print(windows_path)
            file_path = windows_path
            return
        else:
            file_path = linux_path
        print(file_path)
        shutil.move(file_path,f"downloads/{file_name}")
        file_path = f"downloads/{file_name}"
        
        
    # Upload the file to Google Drive with interval-based progress callback
    try:
        file_metadata = {'name': file_name,
                        'parents' : [PARENT_FOLDER_ID]}
        media = MediaFileUpload(file_path, resumable=True)
        request = drive_service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        )
        print("metadata created")

        last_update_time = asyncio.get_event_loop().time()
        done = False
        
        while not done:
            try:
                status, done = request.next_chunk()
                
                if status:
                    #log the progress
                    progress = status.resumable_progress / status.total_size * 100
                    print(f"file upload% = {progress:.1f}")


                    current_time = asyncio.get_event_loop().time()
                    if current_time - last_update_time >= UPLOAD_INTERVAL:
                        await update.message.reply_text(f'Upload progress: {int(progress)}%')
                        last_update_time = current_time

            except Exception as chunk_error:
                print(f"Error during chunk upload: {chunk_error}")
                await update.message.reply_text("Error during file upload. Retrying...")
                await asyncio.sleep(1)  # Brief pause before retry
                continue
            

        # Confirm completion
        uploaded_file = request.execute()
        print(f"Uploaded file with ID: {uploaded_file.get('id')}")
        await update.message.reply_text(f"File uploaded successfully with ID: {uploaded_file.get('id')}")
    except Exception as e:
        print(f"An error occurred: {e}")
        await update.message.reply_text("Failed to upload the file.")
    finally:
         # Cleanup the downloaded file
        await asyncio.sleep(10)  # Small delay to ensure file operations are completed
        print("removing file")
        try:
            os.unlink(file_path)
        except Exception as e:
            print("error while deleting file: ",e)
   
async def stop_bot(app):
    await app.stop()
    await app.shutdown()

# Error handling
async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error: {context.error}')

def validate_env():
    required_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH',
        'LOCAL_API_SERVER',
        'PARENT_FOLDER_ID'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}\n"
            "Please check your .env file"
        )

# Bot setup
if __name__ == '__main__':
    validate_env()
    print('Starting bot...')
    
    app = ApplicationBuilder()\
        .token(BOT_TOKEN)\
        .base_url('http://localhost:8081/bot')\
        .build()

    app.local_mode=True
    app.read_timeout=300

    # Commands
    app.add_handler(CommandHandler('start', start_command))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(CommandHandler('logout', logout_command))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # Error handler
    app.add_error_handler(error)

    #stop_bot(app)
    print('Polling...')
    app.run_polling()
