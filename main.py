import requests
import time
import schedule
from datetime import datetime
from telegram.ext import Updater, CommandHandler

# === CẤU HÌNH ===
TELEGRAM_BOT_TOKEN = "7901340967:AAFag68eBiTwMeDb6a-c6hKi_2R6dhkHNjs"  # BOT TOKEN của bạn
TELEGRAM_CHAT_ID = "1512472602"  # CHAT ID của bạn
CONFIG_FILE = "config.txt"
STATUS_HISTORY_FILE = "video_status_log.txt"
CHECK_INTERVAL_MINUTES = 5

last_statuses = {}  # Lưu trạng thái của từng video

# === ĐỌC VIDEO_ID TỪ FILE CẤU HÌNH ===
def get_video_data():
    try:
        with open(CONFIG_FILE, "r") as f:
            return [line.strip().split(" - ") for line in f.readlines()]
    except FileNotFoundError:
        return []  # Nếu không tìm thấy file, trả về danh sách rỗng

def set_video_data(new_data):
    with open(CONFIG_FILE, "w") as f:
        for name, video_id in new_data:
            f.write(f"{name} - {video_id}\n")

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
            log_status(video_name, video_id, status)
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

# === /setvideo <Tên video> <ID video> ĐỔI VIDEO ===
def handle_setvideo(update, context):
    if len(context.args) < 2:
        update.message.reply_text("⚠️ Bạn cần nhập Tên video và Video ID.\nVD: /setvideo Video1 dQw4w9WgXcQ")
        return
    
    video_name = context.args[0]
    video_id = context.args[1]
    video_data = get_video_data()

    # Kiểm tra nếu video đã có trong danh sách
    if any(v_id == video_id for _, v_id in video_data):
        update.message.reply_text(f"⚠️ Video {video_name} đã có trong danh sách theo dõi.")
    else:
        video_data.append((video_name, video_id))
        set_video_data(video_data)
        update.message.reply_text(f"✅ Đã thêm video '{video_name}' vào danh sách theo dõi.")

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
