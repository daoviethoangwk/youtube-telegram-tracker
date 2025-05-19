import requests
import time
import schedule
from datetime import datetime
from telegram.ext import Updater, CommandHandler

# === CẤU HÌNH ===
TELEGRAM_BOT_TOKEN = "7901340967:AAFag68eBiTwMeDb6a-c6hKi_2R6dhkHNjs"      # ← Thay bằng token bot Telegram
TELEGRAM_CHAT_ID = "1512472602"          # ← Thay bằng chat ID của bạn
CONFIG_FILE = "config.txt"
STATUS_HISTORY_FILE = "video_status_log.txt"
CHECK_INTERVAL_MINUTES = 5

last_statuses = {}  # Lưu trạng thái của từng video

# === ĐỌC VIDEO_ID TỪ FILE CẤU HÌNH ===
def get_video_ids():
    try:
        with open(CONFIG_FILE, "r") as f:
            return [line.strip() for line in f.readlines()]
    except FileNotFoundError:
        return []  # Nếu không tìm thấy file, trả về danh sách rỗng

def set_video_ids(new_ids):
    with open(CONFIG_FILE, "w") as f:
        for video_id in new_ids:
            f.write(video_id + "\n")

def get_youtube_url(video_id):
    return f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"

# === GỬI TELEGRAM ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")

# === GHI LOG TRẠNG THÁI ===
def log_status(video_id, status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] Video {video_id} status: {status}"
    with open(STATUS_HISTORY_FILE, "a") as f:
        f.write(message + "\n")
    print(message)
    send_telegram_message(message)

# === KIỂM TRA TRẠNG THÁI VIDEO ===
def check_video_status():
    global last_statuses
    video_ids = get_video_ids()
    
    for video_id in video_ids:
        try:
            url = get_youtube_url(video_id)
            response = requests.get(url)
            if response.status_code == 200:
                status = "PUBLIC"
            else:
                status = "UNAVAILABLE"
        except Exception:
            status = "ERROR"

        # Nếu trạng thái thay đổi, ghi log và gửi thông báo
        if last_statuses.get(video_id) != status:
            log_status(video_id, status)
            last_statuses[video_id] = status

# === /history LỌC LỊCH SỬ ===
def handle_history(update, context):
    try:
        with open(STATUS_HISTORY_FILE, "r") as f:
            lines = f.readlines()

        if context.args:
            filter_date = context.args[0]
            filtered = [line for line in lines if line.startswith(f"[{filter_date}")]
            if not filtered:
                history_text = f"📂 Không có lịch sử cho ngày {filter_date}."
            else:
                history_text = f"📅 Lịch sử video ngày {filter_date}:\n" + "".join(filtered)
        else:
            history_text = "📄 20 dòng gần nhất:\n" + "".join(lines[-20:])
    except FileNotFoundError:
        history_text = "❌ Không có file log."

    update.message.reply_text(history_text)

# === /setvideo <ID> ĐỔI VIDEO ===
def handle_setvideo(update, context):
    if not context.args:
        update.message.reply_text("⚠️ Bạn cần nhập Video ID.\nVD: /setvideo dQw4w9WgXcQ")
        return
    
    new_id = context.args[0]
    video_ids = get_video_ids()

    if new_id not in video_ids:
        video_ids.append(new_id)
        set_video_ids(video_ids)
        update.message.reply_text(f"✅ Đã thêm video {new_id} vào danh sách theo dõi.")
    else:
        update.message.reply_text(f"⚠️ Video {new_id} đã có trong danh sách theo dõi.")

# === KHỞI ĐỘNG TELEGRAM BOT ===
def setup_bot():
    updater = Updater(token=TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("history", handle_history))
    dp.add_handler(CommandHandler("setvideo", handle_setvideo))
    updater.start_polling()
    return updater

# === LẬP LỊCH KIỂM TRA VIDEO ===
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_video_status)

print("🟢 Đang theo dõi video YouTube...")
check_video_status()
bot_updater = setup_bot()

while True:
    schedule.run_pending()
    time.sleep(1)
