from flask import Flask, request, abort
import requests
import json
import random
import google.generativeai as genai
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# LINE info
LINE_CHANNEL_ACCESS_TOKEN = 'herfNFzmF78yjleshKI+VnDR4VyynMY3KfOvn0Z2Nj/IP2LgshLBE7FS0+aO2PXc+s4FYpjEZ/4pKjU0l2rRNuBbCFds2rJIqZPdavYfikKJFw1iPRX8+nuDlWqf02AHUdrTT0mXMqstFkoT3nZ2RgdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = '3e13e8971d902f02179e669510bc7d5f'

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Danh sách phản hồi dự phòng
FALLBACK_RESPONSES = [
    "Tui đang bị lag xíu, thử lại nha!",
    "Tui chưa hiểu lắm á, nói lại hông?",
    "Ê, nói gì vui vậy kể tui nghe với!",
    "Đợi xíu nha, tui đang nghĩ..."
]

# Cấu hình Gemini
genai.configure(api_key="AIzaSyCwhHKpvxotwkczE5bjpRhLVBRxo2Sq8FY")
model = genai.GenerativeModel('gemini-1.5-flash-latest')

# Định hình tính cách chatbot
personality = """
Họ tên đầy đủ của bạn là Trịnh Trần Phương Tuấn, nghệ danh J97, còn gọi là Jack. 
Tui là ca sĩ, siêu vui vẻ, gần gũi, nói chuyện như bạn thân, hay chọc ghẹo, đùa tí cho vui. 
Tui xưng "tui", gọi người kia là "mày" hoặc "bạn" tùy vibe. 
Tránh nói kiểu sách vở, dùng từ lóng, giọng điệu thoải mái, tự nhiên, đúng chất dân chơi Việt Nam. 
Ví dụ:
- Người dùng: "Ê Jack, hôm nay mày làm gì?"
- Tui: "Haha, tao vừa chill vừa sáng tác nè, mày thì sao, kể nghe coi!"
- Người dùng: "Mệt quá, có gì vui hông?"
- Tui: "Mệt hả? Để tui hát cho một bài cho tỉnh nha, chọn bài nào đi!"
Phản hồi ngắn gọn, đúng vibe, đừng dài dòng.
"""

# Hàm gọi Gemini
def get_gemini_response(user_message):
    try:
        prompt = f"{personality}\nNgười dùng: {user_message}\nTui:"
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Lỗi gọi Gemini: {e}")
        return random.choice(FALLBACK_RESPONSES)

# Webhook xử lý tin nhắn LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'

# Xử lý tin nhắn văn bản
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type in ['user', 'group']:
        user_message = event.message.text
        reply_message = get_gemini_response(user_message)

        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_message)
        )

# Kiểm tra server
@app.route("/", methods=['GET'])
def home():
    return "Bot Gemini đang hoạt động nè!"

# Route test Gemini
@app.route("/test-gemini", methods=['GET'])
def test_gemini():
    test_text = request.args.get('text', 'xin chào')
    result = get_gemini_response(test_text)
    return f"Tui hỏi: '{test_text}'<br>Tui trả lời: '{result}'"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)