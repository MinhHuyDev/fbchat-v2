import requests, json
from _core._utils import formAll, mainRequests, formatResults

def add_remove_admin(facebook_data, thread_id, user_id, add_admin=True):
    form_data = formAll(facebook_data, requireGraphql=False)
    form_data["thread_fbid"] = str(thread_id)
    form_data["admin_ids[0]"] = str(user_id)
    form_data["add"] = add_admin

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/save_admins/?dpr=1", form_data, facebook_data["cookieFacebook"])).text.split("for (;;);")[1])

    if response.get("error"):
        error = response["error"]
        match error:
            case 1976004:
                return formatResults("error", "Bạn không phải là quản trị viên.")
            case 1357031:
                return formatResults("error", "Chủ đề này không phải là một cuộc trò chuyện nhóm.")
            case _:
             return formatResults("error", "Lỗi không xác định.")
    else:
        return formatResults("success", "Thêm admin cho nhóm thành công.")