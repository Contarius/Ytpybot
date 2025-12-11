import telebot
import yt_dlp
import os
import requests

BOT_TOKEN = "8120591733:AAH4tu4uUuCFiixw6S9A8FMcmECwuwHDD2E"
bot = telebot.TeleBot(BOT_TOKEN)


# ---------------------------
# UPLOAD TO GOFILE (НОВА ВЕРСІЯ API)
# ---------------------------
def upload_to_gofile(path):
    try:
        server = requests.get("https://api.gofile.io/getServer").json()["data"]["server"]

        with open(path, "rb") as f:
            r = requests.post(
                f"https://{server}.gofile.io/uploadFile",
                files={"file": f}
            )

        data = r.json()
        if data["status"] == "ok":
            return data["data"]["downloadPage"]

        return None

    except Exception as e:
        print("GoFile error:", e)
        return None


# ---------------------------
# START
# ---------------------------
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Надішли YouTube-посилання 🎬")


# ---------------------------
# ОБРОБКА ПОСИЛАННЯ
# ---------------------------
@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def handle_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Отримую формати...")

    try:
        with yt_dlp.YoutubeDL({"quiet": True}) as ydl:
            info = ydl.extract_info(url, download=False)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ yt-dlp помилка: {e}")
        return

    if not info or "formats" not in info:
        bot.send_message(message.chat.id, "❌ Не знайшов формати.")
        return

    # Показуємо тільки відео формати
    text = "🎬 Доступні формати:\n\n"

    for f in info["formats"]:
        if not f.get("format_id"):
            continue

        # залишаємо тільки формати mp4
        if f.get("ext") != "mp4":
            continue

        # роздільна здатність
        res = f.get("resolution") or "N/A"

        # розмір файлу
        if f.get("filesize"):
            size_mb = round(f["filesize"] / 1024 / 1024)
        else:
            size_mb = "?"

        text += f"{f['format_id']} — {res} — {size_mb} MB\n"

    bot.send_message(message.chat.id, text)
    bot.send_message(message.chat.id, "Введи format_id:")

    bot.register_next_step_handler(message, lambda msg: download_video(msg, url))


# ---------------------------
# ЗАВАНТАЖЕННЯ ВІДЕО
# ---------------------------
def download_video(message, url):
    fmt = message.text.strip()

    bot.send_message(message.chat.id, f"⏳ Завантажую відео ({fmt})...")

    try:
        ydl_opts = {
            "format": f"{fmt}+bestaudio/best",   # ЗАВЖДИ Є ЗВУК
            "outtmpl": "video.mp4",
            "merge_output_format": "mp4",
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка завантаження: {e}")
        return

    size_mb = os.path.getsize("video.mp4") / 1024 / 1024

    # ---------------------------
    # Менше 50 МБ → Telegram
    # ---------------------------
    if size_mb < 49:
        try:
            with open("video.mp4", "rb") as f:
                bot.send_document(message.chat.id, f)
            os.remove("video.mp4")
            return
        except Exception as e:
            bot.send_message(message.chat.id, f"❌ Telegram помилка: {e}")

    # ---------------------------
    # Більше 50 МБ → GoFile
    # ---------------------------
    bot.send_message(message.chat.id, "📤 Файл великий, вантажу на GoFile...")

    link = upload_to_gofile("video.mp4")
    os.remove("video.mp4")

    if link:
        bot.send_message(message.chat.id, f"✔️ Готово!\n🔗 {link}")
    else:
        bot.send_message(message.chat.id, "❌ Не вдалося завантажити на GoFile.")


print("Bot running...")
bot.infinity_polling()