import telebot
import yt_dlp
import os
import requests

BOT_TOKEN = "8120591733:AAH4tu4uUuCFiixw6S9A8FMcmECwuwHDD2E"
bot = telebot.TeleBot(BOT_TOKEN)


def upload_to_gofile(path):
    try:
        server = requests.get("https://api.gofile.io/getServer").json()["data"]["server"]
        r = requests.post(
            f"https://{server}.gofile.io/uploadFile",
            files={"file": open(path, "rb")}
        )
        return r.json()["data"]["downloadPage"]
    except:
        return None


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Надішли YouTube-посилання 🎬")


@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Завантажую інформацію...")

    try:
        ydl_opts = {"quiet": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка yt-dlp: {e}")
        return

    # -----------------------------
    # ПРОВІРКА НА None
    # -----------------------------
    if not info:
        bot.send_message(message.chat.id, "❌ Не вдалося отримати відео. Можливо, потрібно кукі.")
        return

    if "formats" not in info or not info["formats"]:
        bot.send_message(message.chat.id, "❌ Формати не знайдені.")
        return

    formats_text = "Оберіть якість:\n\n"

    for f in info["formats"]:
        if f.get("filesize") and f.get("format_id"):
            size_mb = round(f["filesize"] / 1024 / 1024)
            res = f.get("resolution") or "N/A"
            formats_text += f"{f['format_id']} — {res} — {size_mb} MB\n"

    bot.send_message(message.chat.id, formats_text)
    bot.send_message(message.chat.id, "Введи format_id:")
    bot.register_next_step_handler(message, lambda msg: download_video(msg, url))


def download_video(message, url):
    fmt = message.text.strip()
    bot.send_message(message.chat.id, f"⏳ Завантажую відео ({fmt})...")

    try:
        ydl_opts = {
            "format": fmt,
            "outtmpl": "video.mp4",
            "merge_output_format": "mp4",
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка завантаження: {e}")
        return

    size_mb = os.path.getsize("video.mp4") / 1024 / 1024

    # -----------------------------
    # МЕНШЕ 50 МБ → В TELEGRAM
    # -----------------------------
    if size_mb < 49:
        try:
            with open("video.mp4", "rb") as f:
                bot.send_document(message.chat.id, f)
            os.remove("video.mp4")
            return
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Telegram помилка: {e}")

    # -----------------------------
    # БІЛЬШЕ 50 МБ → GOFILE
    # -----------------------------
    bot.send_message(message.chat.id, "📤 Файл великий, вантажу на GoFile...")
    link = upload_to_gofile("video.mp4")
    os.remove("video.mp4")

    if link:
        bot.send_message(message.chat.id, f"✔️ Готово!\n🔗 {link}")
    else:
        bot.send_message(message.chat.id, "❌ Не вдалося завантажити на GoFile.")


print("Bot is running...")
bot.infinity_polling()