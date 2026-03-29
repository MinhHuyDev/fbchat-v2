import json, requests
from _core._utils import formAll, mainRequests, formatResults

def change_user_nickname(facebook_data, thread_id, user_id, new_nickname): # Thay đổi biệt danh người dùng

    form_data = formAll(facebook_data, requireGraphql=False)
    form_data["nickname"] = new_nickname
    form_data["participant_id"] = user_id
    form_data["thread_or_other_fbid"] = str(thread_id)

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/save_thread_nickname/?source=thread_settings&dpr=1", form_data, facebook_data["cookieFacebook"])).text.split("for (;;);")[1])


    if response.get("error"):
        match response.get("error"):
            case 1545014:
                return formatResults("error", "Người dùng không tồn tại trong nhóm/cuộc trò chuyện.")
            case 1357031:
                return formatResults("error", "Người dùng không tồn tại.")
            case _:
                return formatResults("error", "Lỗi không xác định.")
    else:
        return formatResults("success", "Thay đổi biệt danh người dùng thành công.")