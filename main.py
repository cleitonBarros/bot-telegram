import os
import asyncio
from os import getenv
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pathlib import Path
from dotenv import load_dotenv
from pyrogram import Client, filters

# 🔥 NOVO
from flask import Flask
import threading

load_dotenv()

# Configuração de diretórios
SCRIPT_DIR = Path(__file__).parent
VIDEO_DIR = SCRIPT_DIR / "videos"
VIDEO_DIR.mkdir(exist_ok=True)

# Flask app (abre porta pro Render)
web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "Bot está rodando!"


@web_app.route("/health")
def health():
    return "ok", 200

# Bot Telegram
app = Client(
    "downVideos",
    api_id=getenv("TELEGRAM_API_ID"),
    api_hash=getenv("TELEGRAM_API_HASH"),
    bot_token=getenv("TELEGRAM_BOT_TOKEN")
)

def has_link(_, __, message):
    if message.text:
        return "http://" in message.text or "https://" in message.text
    return False

link_filter = filters.create(has_link)

async def video_downloader(client, message, video_link):
    try:
        await message.reply("📥 Verificando vídeo...")

        # 🔥 Fallback automático (WEB → ANDROID)
        try:
            video_url = YouTube(
                video_link,
                on_progress_callback=on_progress,
                client="WEB"
            )
        except Exception:
            try:
                video_url = YouTube(
                    video_link,
                    on_progress_callback=on_progress,
                    client="ANDROID"
                )
            except Exception as e:
                await message.reply(f"❌ Erro ao acessar vídeo: {str(e)}")
                return

        if video_url.length > 450:
            await message.reply(
                f"⚠️ O vídeo passou do limite!\n\n"
                f"🎬 {video_url.title}\n"
                f"⏱ Duração: {video_url.length}s ({video_url.length // 60} minutos)\n\n"
                f"❌ Limite máximo: 7 minutos"
            )
            return

        await message.reply("📥 Baixando vídeo...")

        # 🔥 melhoria: evita erro em streams separados
        video = video_url.streams.filter(progressive=True).get_highest_resolution()

        downloaded_file = video.download(output_path=str(VIDEO_DIR))

        await message.reply("🔄 Convertendo! Pode levar alguns minutos...")

        await message.reply_video(
            video=downloaded_file,
            caption=f"🎬 {video_url.title}\n⏱ Duração: {video_url.length}s\n📺 Resolução: {video.resolution}"
        )

        os.remove(downloaded_file)

    except Exception as e:
        await message.reply(f"❌ Erro ao baixar: {str(e)}")


@app.on_message(link_filter)
async def link_handler(client, message):
    await video_downloader(client, message, message.text)

@app.on_message(~link_filter)
async def handle_message(client, message):
    print(message.chat.username, message.text)
    await message.reply("Mensagem recebida nao é um link, por favor envie um link!")

# 🔥 roda Flask em paralelo
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Inicia Flask em thread separada
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Roda bot na thread principal (necessário para signal handlers)
    app.run()