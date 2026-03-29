import json, requests, time, random
from unittest import case
from _core._utils import formAll, mainRequests, formatResults

def change_thread_name(facebook_data, thread_id, new_thread_name): # Thay đổi tên nhóm

    random_number = str(int(format(int(time.time() * 1000), "b") + ("0000000000000000000000" + format(int(random.random() * 4294967295), "b"))[-22:], 2))

    form_data = formAll(facebook_data, requireGraphql=False)
    form_data["client"] = "mercury"
    form_data["action_type"] = "ma-type:log-message"
    form_data["thread_id"] = ""
    form_data["author_email"] = ""
    form_data["action_type"] = ""
    form_data["timestamp"] = int(time.time() * 1000)
    form_data["timestamp_absolute"] = "Today"
    form_data["author"] = "fbid:" + str(facebook_data["FacebookID"])
    form_data["is_unread"] = False
    form_data["is_cleared"] = False
    form_data["is_forward"] = False
    form_data["is_filtered_content"] = False
    form_data["is_filtered_content_bh"] = False
    form_data["is_filtered_content_account"] = False
    form_data["is_filtered_content_quasar"] = False
    form_data["is_filtered_content_invalid_app"] = False
    form_data["is_spoof_warning"] = False
    form_data["thread_fbid"] = str(thread_id)
    form_data["thread_name"] = new_thread_name
    form_data["thread_id"] = str(thread_id)
    form_data["source"] = "source:chat:web"
    form_data["source_tags[0]"] = "source:chat"
    form_data["client_thread_id"] = "root:" + random_number
    form_data["offline_threading_id"] = random_number
    form_data["message_id"] = random_number
    form_data["threading_id"] = "<{}:{}-{}@mail.projektitan.com>".format(int(time.time() * 1000), int(random.random() * 4294967295), hex(int(random.random() * 2 ** 31))[2:])
    form_data["ephemeral_ttl_mode"] = "0"
    form_data["manual_retry_cnt"] = "0"
    form_data["ui_push_phase"] = "V3"
    form_data["log_message_type"] = "log:thread-name"
    # form_data["thread_name"] = new_thread_name
    # form_data["thread_id"] = self.thread_id


    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/set_thread_name/", form_data, facebook_data["cookieFacebook"])).text.split("for (;;);")[1])

    if (response.get("error")):
        match response.get("error"):
            case 1545012:
                return formatResults("error", "Bạn không thể thay đổi tên nhóm khi bạn không phải là một thành viên của nhóm.")
            case 1545003:
                return formatResults("error", "Không thể thay đổi tên nhóm không tồn tại.")
    else:
        return formatResults("error", "Thay đổi tên nhóm thành công.")