import os 
from os import getenv
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pathlib import Path
from dotenv import load_dotenv
from pyrogram import Client, filters

load_dotenv()

# Configuração de diretórios
SCRIPT_DIR = Path(__file__).parent
VIDEO_DIR = SCRIPT_DIR / "videos"
VIDEO_DIR.mkdir(exist_ok=True)  # Cria o diretório se não existir


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

# async def video_downloader(message_text):
    # while True:
    #     video_link = message_text.strip()
        
    #     # Validação corrigida
    #     if not video_link.startswith("https://"):
    #         print("Link inválido! Use um link do YouTube válido (https://...)")
    #         continue
            
    #     try:
    #         print("Downloading...")
    #         video_url = YouTube(video_link, on_progress_callback=on_progress)
    #         print(f"Título: {video_url.title}")
    #         print(f"Duração: {video_url.length} segundos")
            
    #         # Mostrar resoluções disponíveis
    #         print("\nResoluções disponíveis:")
    #         streams = video_url.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
            
    #         for i, stream in enumerate(streams, 1):
    #             print(f"{i}. {stream.resolution} - {stream.fps}fps - {round(stream.filesize / (1024*1024), 2)}MB")
            
    #         video = video_url.streams.get_highest_resolution()
            
    #         print(f"\n📥 Baixando em {video.resolution}...")
    #         path_to_download = r'C:\Users\cleit\Downloads'
            
    #         print(f"Baixando para: {path_to_download}")
    #         video.download(output_path="videos")
            
    #         print("✓ Video Downloaded Successfully!")
    #         startfile(r"C:\Users\cleit\Downloads")
    #         break
            
    #     except Exception as e:
    #         print(f"Erro ao baixar vídeo: {str(e)}")
    #         print(f"Tipo do erro: {type(e).__name__}")
    #         retry = input("Tentar outro link? (s/n): ").lower()
    #         if retry != 's':
    #             break

async def video_downloader(client, message, video_link):
    try:
        await message.reply("📥 Verificando vídeo...")
        video_url = YouTube(video_link, on_progress_callback=on_progress)
        
        if video_url.length > 450:
          await message.reply(
            f"⚠️ O vídeo passou do limite!\n\n"
            f"🎬 {video_url.title}\n"
            f"⏱ Duração: {video_url.length}s ({video_url.length // 60} minutos)\n\n"
            f"❌ Limite máximo: 7 minutos"
          )
          return

        await message.reply("📥 Baixando vídeo...")

        video = video_url.streams.get_highest_resolution()
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

@app.on_message()
async def handle_message(client, message):
    print(message.chat.username, message.text)
    await message.reply("Mensagem recebida nao e um link, por favor envie um link!")

app.run()