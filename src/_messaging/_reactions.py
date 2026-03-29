import requests, json
from _core._utils import Headers, parse_cookie_string, formAll
     
def add_remove_reaction(facebook_data, reaction_type, message_id, emoji_choice):

     form_data = formAll(facebook_data, docID=1491398900900362)
     form_data["variables"] = json.dumps({"data": {
          "action": "ADD_REACTION" if (reaction_type == "add") else "REMOVE_REACTION",
          "client_mutation_id": "1",
          "actor_id": facebook_data["FacebookID"],
          "message_id": str(message_id),
          "reaction": emoji_choice # random.choice(["🥺","😏", "✅","😎","😭", "🫥", "✈️", "✅", "🌚", "😵", "😮‍💨", "😷", "🥹", "😒", "🐧", "💩", "🍦", "👀", "💀", "🐣", "💔", "🫶🏻", "🪐", "🙈", "🐈‍⬛", "🦆", "🔪", "⚙️", "🧭", "📡", "💌", "⁉️", "💀"])
     }})
     form_data["dpr"] = 1

     request_params = {
               "headers": Headers(facebook_data["cookieFacebook"], form_data),
               "timeout": 60000,
               "url": "https://www.facebook.com/webgraphql/mutation/",
               "data": form_data,
               "cookies": parse_cookie_string(facebook_data["cookieFacebook"]),
               "verify": True
     }

     response = requests.post(**request_params)
     return response
     

""" Hướng dẫn sử dụng (Tutorial)

 * Dữ liệu yêu cầu (args):

     - dataFB: lấy từ __facebookToolsV2.dataGetHome(setCookies)
     - setCookies: Cookie account Facebook
     - typeAdded: "add" thêm reaction vào tin nhắn đó. "remove" để xoá reaction tại tin nhắn đó
     - messageID: messageID của tin nhắn
     - emojiChoice: emoji cần reaction vào tin nhắn (VD: 👍, 😭, 😎,....)(All emoji)

* Kết quả trả về:

     - Không có dữ liệu
     - Ghi chú: tùy thuộc vào nhiều trường hợp mà error có thể báo code lỗi và chi tiết khác nhau!

* Thông tin tác giả:
     Facebook:  m.me/Booking.MinhHuyDev
     Telegram: t.me/minhhuydev
     Github: MinhHuyDev

✓Remake by Nguyễn Minh Huy
✓Remake from Fbchat Python (https://fbchat.readthedocs.io/en/stable/)
✓Hoàn thành vào lúc 21:22 ngày 23/6/2023 • Cập nhật mới nhất: 7:52 20/7/2023
✓Tôn trọng tác giả ❤️
"""
