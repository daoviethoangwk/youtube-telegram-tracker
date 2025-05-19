from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import requests
import time
import schedule
from datetime import datetime

# === CẤU HÌNH ===
TELEGRAM_BOT_TOKEN = "7901340967:AAFag68eBiTwMeDb6a-c6hKi_2R6dhkHNjs"
TELEGRAM_CHAT_ID = "1512472602"
CONFIG_FILE = "config.txt"
STATUS_HISTORY_FILE = "video_status_log.txt"
CHECK_INTERVAL_MINUTES = 5

last_statuses = {}

# === ĐỌC & GHI FILE ===
def get_video_data():
    try:
        with open(CONFIG_FILE, "r") as f:
            return [line.strip().split(" - ")[1:] for line in f.readlines()]
    except FileNotFoundError:
        return []

def set_video_data(new_data):
    with open(CONFIG_FILE, "w") as f:
        for idx, (name, video_id) in enumerate(new_data, start=1):
            f.write(f"{idx} - {name} - {video_id}\n")

def get_youtube_url(video_id):
    return f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")

def log_status(video_name, video_id, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] Video '{video_name}' (ID: {video_id}) status: {status}"
    with open(STATUS_HISTORY_FILE, "a") as f:
        f.write(message + "\n")
    print(message)
    send_telegram_message(message)

# === KIỂM TRA TRẠNG THÁI VIDEO ===
def check_video_status():
    global last_statuses
    video_data = get_video_data()
    for video_name, video_id in video_data:
        try:
            response = requests.get(get_youtube_url(video_id))
            status = "PUBLIC" if response.status_code == 200 else "UNAVAILABLE"
        except Exception:
            status = "ERROR"
        if last_statuses.get(video_id) != status:
            log_status(video_name, video_id, status)
            last_statuses[video_id] = status

# === COMMAND HANDLERS ===
def handle_start(update: Update, context: CallbackContext):
    reply_keyboard = [["1. Thêm ID theo dõi"], ["2. Kiểm tra danh sách ID"]]
    markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True, one_time_keyboard=True)
    update.message.reply_text(
        "👋 Chào bạn! Hãy chọn thao tác:",
        reply_markup=markup
    )

def handle_text(update: Update, context: CallbackContext):
    text = update.message.text.strip()
    if text == "1. Thêm ID theo dõi":
        update.message.reply_text("📝 Gửi lệnh:\n/setvideo <TênVideo> <VideoID>")
    elif text == "2. Kiểm tra danh sách ID":
        reply_keyboard = [['2.1. Xem danh sách hiện có'], ['2.2. Xóa ID theo số thứ tự']]
        markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        update.message.reply_text("📋 Bạn muốn làm gì tiếp theo?", reply_markup=markup)
    elif text == "2.1. Xem danh sách hiện có":
        handle_list(update, context)
    elif text == "2.2. Xóa ID theo số thứ tự":
        update.message.reply_text("❌ Gửi lệnh:\n/remove <SốThứTự>")
    else:
        update.message.reply_text("⚠️ Không rõ yêu cầu. Dùng /start để hiển thị menu.")

def handle_setvideo(update: Update, context: CallbackContext):
    if len(context.args) < 2:
        update.message.reply_text("⚠️ Gửi lệnh đúng cú pháp:\n/setvideo <TênVideo> <VideoID>")
        return
    name, video_id = context.args[0], context.args[1]
    video_data = get_video_data()
    if any(vid == video_id for _, vid in video_data):
        update.message.reply_text("⚠️ Video đã tồn tại.")
    else:
        video_data.append((name, video_id))
        set_video_data(video_data)
        update.message.reply_text(f"✅ Đã thêm video: {name} (ID: {video_id})")

def handle_list(update: Update, context: CallbackContext):
    video_data = get_video_data()
    if not video_data:
        update.message.reply_text("📭 Danh sách rỗng.")
        return
    msg = "📋 Danh sách video:\n"
    for idx, (name, vid) in enumerate(video_data, start=1):
        msg += f"{idx}. {name} (ID: {vid})\n"
    update.message.reply_text(msg)

def handle_remove(update: Update, context: CallbackContext):
    if len(context.args) < 1:
        update.message.reply_text("⚠️ Gửi lệnh đúng cú pháp:\n/remove <SốThứTự>")
        return
    try:
        idx = int(context.args[0]) - 1
    except ValueError:
        update.message.reply_text("⚠️ Số không hợp lệ.")
        return
    video_data = get_video_data()
    if 0 <= idx < len(video_data):
        removed = video_data.pop(idx)
        set_video_data(video_data)
        update.message.reply_text(f"✅ Đã xóa: {removed[0]} (ID: {removed[1]})")
    else:
        update.message.reply_text("❌ Không tìm thấy video.")

def handle_history(update: Update, context: CallbackContext):
    try:
        with open(STATUS_HISTORY_FILE, "r") as f:
            lines = f.readlines()
        if context.args:
            date = context.args[0]
            filtered = [l for l in lines if l.startswith(f"[{date}")]
            msg = "\n".join(filtered) or f"📂 Không có lịch sử cho ngày {date}."
        else:
            msg = "📄 20 dòng gần nhất:\n" + "".join(lines[-20:])
    except FileNotFoundError:
        msg = "📁 Không tìm thấy file lịch sử."
    update.message.reply_text(msg)

# === CHẠY BOT TELEGRAM ===
def setup_bot():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", handle_start))
    dp.add_handler(CommandHandler("setvideo", handle_setvideo))
    dp.add_handler(CommandHandler("list", handle_list))
    dp.add_handler(CommandHandler("remove", handle_remove))
    dp.add_handler(CommandHandler("history", handle_history))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    updater.start_polling()
    return updater

# === LẬP LỊCH KIỂM TRA VIDEO ĐỊNH KỲ ===
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_video_status)
check_video_status()
bot_updater = setup_bot()

print("🟢 Bot đã khởi động và theo dõi video YouTube...")

while True:
    schedule.run_pending()
    time.sleep(1)
