from flask import Flask, request, abort
import logging
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, PostbackEvent, TextMessage, TextSendMessage, FlexSendMessage

app = Flask(__name__)

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LINE info
LINE_CHANNEL_ACCESS_TOKEN = 'mf1SA+Go407sKuw3xMI9qnylkLb822PcMCZa6NNRYx3x0cP8opUdMlrLrhmAEI4oy8kNMUxhQav1i54x8G8qkO4RZVebj6FMtFDaBDdZVXOkbtKmo4w9AOqbNIEiUXFWzum8tsFb3kq8y9xlKKgt5AdB04t89/1O/w1cDnyilFU='
LINE_CHANNEL_SECRET = 'c5771c686254e1e0d75f0ef65180b1da'

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

# Hàm gọi phản hồi cho tin nhắn
def get_message_response(user_message):
    if user_message == '!menu':
        try:
            return FlexSendMessage(alt_text="Menu", contents=MENU_FLEX_MESSAGE)
        except Exception as e:
            logger.error(f"Error creating FlexSendMessage: {str(e)}")
            return TextSendMessage(text="Lỗi khi hiển thị menu, vui lòng thử lại!")
    return TextSendMessage(text="Vui lòng gửi '!menu' để xem menu!")

# Hàm gọi phản hồi cho postback
def get_postback_response(postback_data):
    if postback_data == "action=inventory_check":
        return TextSendMessage(text="Tồn kho hiện tại: 100 sản phẩm")
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
            line_bot_api.reply_message(event.reply_token, reply_message)
        except LineBotApiError as e:
            logger.error(f"LINE API error: {str(e)}")
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
    app.run(host='0.0.0.0', port=8000, debug=True)