import telebot
import yt_dlp
import os

BOT_TOKEN = "8120591733:AAGqydWl4UMhxPlsnrLoI376JlCFkzHByHc"

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id,
        "👋 Привіт! Надішли мені посилання на YouTube."
    )

@bot.message_handler(func=lambda m: "youtube.com" in m.text or "youtu.be" in m.text)
def process_link(message):
    url = message.text.strip()
    bot.send_message(message.chat.id, "⏳ Отримую інформацію...")

    try:
        ydl_opts = {"listformats": True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}")
        return

    if not info or not isinstance(info, dict):
        bot.send_message(message.chat.id, "❌ Не вдалося отримати інформацію про відео.")
        return

    formats = info.get("formats", [])
    quality_list = []

    for f in formats:
        if f.get("ext") == "mp4" and f.get("height") and f["height"] <= 480:
            q = f"{f['format_id']} — {f['height']}p"
            quality_list.append(q)

    if not quality_list:
        bot.send_message(message.chat.id, "❌ Немає доступних легких MP4 форматів.")
        return

    text = "🎬 *Доступні якості:* \n\n"
    for q in quality_list:
        text += "• " + q + "\n"

    bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.send_message(message.chat.id, "🔽 Напиши *format_id* для завантаження.", parse_mode="Markdown")

    bot.register_next_step_handler(message, lambda msg: download_video(msg, url))


def download_video(message, url):
    format_id = message.text.strip()
    bot.send_message(message.chat.id, f"⏳ Завантажую формат {format_id}...")

    try:
        ydl_opts = {
            # Беремо або вибраний формат + аудіо, або автоматично кращий відео+аудіо
            "format": f"{format_id}+bestaudio/best",
            "outtmpl": "video.mp4",
            "merge_output_format": "mp4",  # об'єднує аудіо+відео
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}")
        return

    try:
        with open("video.mp4", "rb") as f:
            # Відправляємо як документ, щоб не втратити звук
            bot.send_document(message.chat.id, f)

        os.remove("video.mp4")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Не вдалося надіслати відео: {e}")

print("🚀 Bot is running...")
bot.infinity_polling()