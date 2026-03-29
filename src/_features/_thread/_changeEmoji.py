import requests, json
from _core._utils import formAll, mainRequests, formatResults

def change_thread_emoji(facebook_data, thread_id, new_emoji): # Thay đổi biểu tượng cảm xúc của nhóm
    form_data = formAll(facebook_data, requireGraphql=False)
    form_data["emoji_choice"] = new_emoji
    form_data["thread_or_other_fbid"] = thread_id

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/save_thread_emoji/?source=thread_settings&__pc=EXP1%3Amessengerdotcom_pkg", form_data, facebook_data["cookieFacebook"])).text.split("for (;;);")[1])

    if (response.get("error")):
        error = response.get("error")
        if error == 1357031:
            return formatResults("error", "Không thể thay đổi trạng thái emoji của một cuộc trò chuyện không tồn tại.")
        else:
            return formatResults("error", "Lỗi không xác định.")
    else:
            return formatResults("success", "Thay đổi biểu tượng cảm xúc nhanh thành công.")