import os
import yt_dlp
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Render-ന് വേണ്ടി ഒരു ലളിതമായ വെബ് സെർവർ
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is Running!")

def run_health_check():
    port = int(os.environ.get('PORT', 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

TOKEN = os.getenv('BOT_TOKEN')

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
        'ffmpeg_location': '/usr/bin/ffmpeg',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info).replace('.webm', '.mp3').replace('.m4a', '.mp3')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 സ്വാഗതം! YouTube ലിങ്ക് അയക്കൂ, ഞാൻ അത് MP3 ആക്കി തരാം.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if "youtube.com" in url or "youtu.be" in url:
        status_msg = await update.message.reply_text("പ്രോസസ്സ് ചെയ്യുന്നു... ⏳")
        try:
            file_path = download_audio(url)
            await update.message.reply_audio(audio=open(file_path, 'rb'))
            os.remove(file_path)
            await status_msg.delete()
        except Exception as e:
            await update.message.reply_text(f"Error: {e}")

def main():
    # വെബ് സെർവർ സ്റ്റാർട്ട് ചെയ്യുന്നു
    threading.Thread(target=run_health_check, daemon=True).start()
    
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == '__main__':
    main()
