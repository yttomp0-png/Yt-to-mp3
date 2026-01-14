import os
import yt_dlp
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Health Check Server for Render to prevent sleeping
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

def run_health_check():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# Your Bot Token
TOKEN = '7926824723:AAGtL4cs5QxxPYndMyWrSgsk_aNnlnCeAKc'

def download_audio(url):
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'ffmpeg_location': '/usr/bin/ffmpeg', # Path for Docker
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! Send me a YouTube link, and I will convert it to MP3 for you.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        status_msg = await update.message.reply_text("Processing your request... Please wait ⏳")
        try:
            file_path = download_audio(url)
            await update.message.reply_audio(audio=open(file_path, 'rb'), caption="Downloaded by your bot")
            os.remove(file_path) # Delete file after sending
            await status_msg.delete()
        except Exception as e:
            await update.message.reply_text(f"Sorry, an error occurred: {e}")
    else:
        await update.message.reply_text("Please send a valid YouTube link.")

def main():
    # Start Health Check Server
    threading.Thread(target=run_health_check, daemon=True).start()
    
    # Initialize Application
    app = Application.builder().token(TOKEN).build()
    
    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
