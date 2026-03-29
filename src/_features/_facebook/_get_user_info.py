import json, requests, json
from _core._utils import parse_cookie_string, Headers, formAll

def get_user_info(facebook_data, user_id):

     form_data = formAll(facebook_data, requireGraphql=False)
     form_data["ids[0]"] = user_id


     request_params = {
        "headers": Headers(facebook_data["cookieFacebook"], form_data),
        "timeout": 5,
        "url": "https://www.facebook.com/chat/user_info/",
        "data": form_data,
        "cookies": parse_cookie_string(facebook_data["cookieFacebook"]),
        "verify": True
    }

     response = requests.post(**request_params)
     try:
        json_data = json.loads(response.text.split("for (;;);")[1])["payload"]["profiles"][str(user_id)]

        user_id_value = json_data.get("id")
        user_name = json_data.get("name")
        first_name = json_data.get("firstName")
        username = json_data.get("vanity")
        thumbnail_src = json_data.get("thumnSrc")
        profile_url = json_data.get("uri")
        user_gender = json_data.get("gender")
        alternate_name = json_data.get("alternateName")
        chat_with_user_is_non_friend = json_data.get("is_nonfriend_messenger_contact")

        if (user_gender == 1): user_gender = "Female (Nữ)"
        elif (user_gender == 2): user_gender = "Male (Nam)"
        else: user_gender = "Unknown (Không xác định)"

        return {
            "idUser": user_id_value,
            "nameUser": user_name,
            "firstName": first_name,
            "Username": username,
            "thumbSrc": thumbnail_src,
            "urlProfile": profile_url,
            "genderUser": user_gender,
            "alternateName": alternate_name,
            "chatWithUSerIsNonFriend": chat_with_user_is_non_friend
        }
     except:
          return {
               "err": 0
          }


""" Hướng dẫn sử dụng (Tutorial)

 * Dữ liệu yêu cầu (args):

     - dataFB: lấy từ __facebookToolsV2.dataGetHome(setCookies)
     - setCookies: Cookie account Facebook
     - userID: ID người dùng cần lấy thông tin

* Kết quả trả về:

     - Khi lấy dữ liệu thành công:

        {'idUser': '1...', 'nameUser': 'Priscilla......', ........}

     - Khi lấy dữ liệu thất bại:

        {'err': 0}

     - Ghi chú: nếu không hiểu gì hãy ib tui nhé hehe.

* Thông tin tác giả:
     Facebook:  m.me/Booking.MinhHuyDev
     Telegram: t.me/minhhuydev
     Github: MinhHuyDev

✓Remake by Nguyễn Minh Huy
✓Remake from Fbchat Python (https://fbchat.readthedocs.io/en/stable/)
✓Hoàn thành vào lúc 18:43 ngày 27/6/2023 • Cập nhật mới nhất: 7:16 20/7/2023
✓Tôn trọng tác giả ❤️
"""
