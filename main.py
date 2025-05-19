import requests
import time
import schedule
from datetime import datetime

# === CẤU HÌNH ===
VIDEO_ID = "nSXh0cnr1LA"  # Thay bằng video ID bạn muốn theo dõi
TELEGRAM_BOT_TOKEN = "7901340967:AAFag68eBiTwMeDb6a-c6hKi_2R6dhkHNjs"  # Thay bằng token bot
TELEGRAM_CHAT_ID = "1512472602"  # Thay bằng chat ID cá nhân của bạn

CHECK_INTERVAL_MINUTES = 5
STATUS_HISTORY_FILE = "video_status_log.txt"
YOUTUBE_VIDEO_URL = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={VIDEO_ID}&format=json"

last_status = None

# === GỬI TIN NHẮN TELEGRAM ===
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }
    try:
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print("⚠️ Gửi Telegram thất bại:", response.text)
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram: {e}")

# === GHI LỊCH SỬ ===
def log_status(status):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"[{timestamp}] Video status: {status}"
    with open(STATUS_HISTORY_FILE, "a") as f:
        f.write(message + "\n")
    print(message)
    send_telegram_message(message)

# === KIỂM TRA VIDEO ===
def check_video_status():
    global last_status
    try:
        response = requests.get(YOUTUBE_VIDEO_URL)
        if response.status_code == 200:
            status = "PUBLIC"
        else:
            status = "UNAVAILABLE"
    except Exception as e:
        status = "ERROR"

    if status != last_status:
        log_status(status)
        last_status = status

# === CHẠY ĐỊNH KỲ ===
schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_video_status)

print("🟢 Đang theo dõi video YouTube...")
check_video_status()

while True:
    schedule.run_pending()
    time.sleep(1)

