from flask import Flask, request, abort
import logging
import os
import pandas as pd
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage, FlexSendMessage
import re

app = Flask(__name__)

# Cấu hình logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),  # Ghi log vào file bot.log
        logging.StreamHandler()  # In log ra console (tùy chọn)
    ]
)
logger = logging.getLogger(__name__)

# LINE info (lấy từ biến môi trường cho bảo mật)
LINE_CHANNEL_ACCESS_TOKEN = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', 'mf1SA+Go407sKuw3xMI9qnylkLb822PcMCZa6NNRYx3x0cP8opUdMlrLrhmAEI4oy8kNMUxhQav1i54x8G8qkO4RZVebj6FMtFDaBDdZVXOkbtKmo4w9AOqbNIEiUXFWzum8tsFb3kq8y9xlKKgt5AdB04t89/1O/w1cDnyilFU=')
LINE_CHANNEL_SECRET = os.getenv('LINE_CHANNEL_SECRET', 'c5771c686254e1e0d75f0ef65180b1da')

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Flex Message với postback action
MENU_FLEX_MESSAGE = {
    "type": "bubble",
    "header": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "text",
                "text": "Menu",
                "weight": "bold",
                "size": "xl",
                "color": "#FFFFFF",
                "align": "center"
            }
        ],
        "backgroundColor": "#1DB446"
    },
    "body": {
        "type": "box",
        "layout": "vertical",
        "contents": [
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "Báo cáo doanh thu",
                    "data": "action=revenue_report"
                },
                "style": "primary",
                "color": "#1DB446",
                "margin": "sm"
            },
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "Review sức bán",
                    "data": "action=sales_review"
                },
                "style": "primary",
                "color": "#1DB446",
                "margin": "sm"
            },
            {
                "type": "button",
                "action": {
                    "type": "postback",
                    "label": "Kiểm tra tồn kho",
                    "data": "action=inventory_check"
                },
                "style": "primary",
                "color": "#1DB446",
                "margin": "sm"
            }
        ],
        "paddingAll": "md"
    }
}

# Hàm đọc file dữ liệu và tính toán tồn kho
def calculate_info():
    try:
        # Đọc file inventory.csv
        df = pd.read_csv('inventory.csv')
        total_quantity = df['quantity'].sum()
        return f"Tồn kho hiện tại: {total_quantity} sản phẩm"
    
    except FileNotFoundError:
        logger.error("File inventory.csv not found")
        return "Lỗi: Không tìm thấy file dữ liệu!"
    except Exception as e:
        logger.error(f"Error reading inventory file: {str(e)}")
        return "Lỗi khi xử lý dữ liệu tồn kho!"


# Hàm data_thuysan (từ yêu cầu trước)
def data_thuysan(store_keyword):
    try:
        df = pd.read_csv('data_thuysan.csv')
        df_kq = df[df['Mã siêu thị'] == store_keyword]
        if df_kq.empty:
            return f"Không có dữ liệu cho siêu thị {store_keyword} trong file 'data_thuysan.csv'."
        sl_nhap = int(df_kq['Nhập'].sum())
        sl_ban = int(df_kq['Bán'].sum())
        rate_NG_nhap = df_kq['Tỉ lệ NG/Nhập'].str.rstrip('%').astype(float).mean()
        rate_NG_nhap = round(rate_NG_nhap)
        sl_huy_kk = int(df_kq['Huỷ và KK'].sum())
        loi_nhuan = int(df_kq['Lợi nhuận'].sum())
        loi_nhuan_formatted = "{:,}".format(loi_nhuan)
        result = (f'Nhóm thuỷ sản, Siêu thị {store_keyword} theo dữ liệu 1 tuần gần nhất:\n'
                  f'- Nhập: {sl_nhap}\n'
                  f'- Bán: {sl_ban}\n'
                  f'- Tỉ lệ NG/Nhập: {rate_NG_nhap}%\n'
                  f'- Huỷ và KK: {sl_huy_kk}\n'
                  f'- Lợi nhuận: {loi_nhuan_formatted}')
        return result
    except FileNotFoundError:
        return "File 'data_thuysan.csv' không tìm thấy. Vui lòng kiểm tra lại!"
    except Exception as e:
        return f"Lỗi khi xử lý dữ liệu siêu thị {store_keyword}: {str(e)}"

# Hàm gọi phản hồi cho tin nhắn
def get_message_response(user_message):
    if user_message == '!menu':
        try:
            return FlexSendMessage(alt_text="Menu", contents=MENU_FLEX_MESSAGE)
        except Exception as e:
            logger.error(f"Error creating FlexSendMessage: {str(e)}")
            return TextSendMessage(text="Lỗi khi hiển thị menu, vui lòng thử lại!")
    if 'tôm' in user_message.lower():
        return TextSendMessage(text="meow")
    
    if '!' in user_message:
            # Extract the first sequence of digits using regex
            match = re.search(r'\d+', user_message)
            if match:
                store_number = int(match.group())  # Convert to integer
                # Call data_thuysan with the extracted number
                result = data_thuysan(store_number)
                return TextSendMessage(text=result)
    

# Hàm gọi phản hồi cho postback
def get_postback_response(postback_data):
    if postback_data == "action=inventory_check":
        return TextSendMessage(text=calculate_info())
    elif postback_data == "action=revenue_report":
        return TextSendMessage(text="Doanh thu hôm nay: 10,000,000 VND (dữ liệu mẫu)")
    elif postback_data == "action=sales_review":
        return TextSendMessage(text="Sức bán ổn định, tăng 5% so với tuần trước (dữ liệu mẫu)")
    return TextSendMessage(text="Hành động không được hỗ trợ!")

# Webhook xử lý tin nhắn LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        logger.error("Invalid signature")
        abort(400)
    except Exception as e:
        logger.error(f"Error in callback: {str(e)}")
        abort(500)

    return 'OK'

# Xử lý tin nhắn văn bản
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if event.source.type in ['user', 'group']:
        user_message = event.message.text
        try:
            reply_message = get_message_response(user_message)
            if reply_message is None:
                logger.info(f"Ignoring message: {user_message}")
                return  # Không gửi phản hồi nếu reply_message là None
            line_bot_api.reply_message(event.reply_token, reply_message)
        except LineBotApiError as e:
            logger.error(f"LINE API error: {str(e)}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Lỗi API LINE, vui lòng thử lại!")
            )
        except Exception as e:
            logger.error(f"Error handling message: {str(e)}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Có lỗi xảy ra, vui lòng thử lại!")
            )

# Xử lý sự kiện postback
@handler.add(PostbackEvent)
def handle_postback(event):
    if event.source.type in ['user', 'group']:
        postback_data = event.postback.data
        try:
            reply_message = get_postback_response(postback_data)
            line_bot_api.reply_message(event.reply_token, reply_message)
        except LineBotApiError as e:
            logger.error(f"LINE API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling postback: {str(e)}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="Có lỗi xảy ra, vui lòng thử lại!")
            )

# Kiểm tra server
@app.route("/", methods=['GET'])
def home():
    return "Bot Line đang hoạt động nè!"

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)