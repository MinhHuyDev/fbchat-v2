import requests, random, time, json
from _core._utils import formAll, mainRequests

def get_all_thread_data(facebook_data): # Lấy dữ liệu những thành phần tin nhắn ở INBOX

    random_number = str(int(format(int(time.time() * 1000), "b") + ("0000000000000000000000" + format(int(random.random() * 4294967295), "b"))[-22:], 2))
    form_data = formAll(facebook_data, requireGraphql=0)
    # form_data["av"] = facebook_data["cookieFacebook"].split("c_user=")[1].split(";")[0]

    form_data["queries"] = json.dumps({
        "o0": {
            "doc_id": "3336396659757871",
            "query_params": {
                    "limit": 50,
                    "before": None,
                    "tags": ["INBOX"], # INBOX, PENDING, ARCHIVED
                    "includeDeliveryReceipts": False,
                    "includeSeqID": True,
            }
        }
    })

    response = requests.post(**mainRequests("https://www.facebook.com/api/graphqlbatch/", form_data, facebook_data["cookieFacebook"]))
    # return response.text.split("{\"successful_results\"")[0]
    response_data = response.text.split('{"successful_results"')[0]
    processing_time = response.elapsed.total_seconds()
    last_seq_id = json.loads(response_data)["o0"]["data"]["viewer"]["message_threads"]["sync_sequence_id"]
    try:
        thread_id_list = []
        thread_name_list = []

        thread_data = json.loads(response_data)["o0"]["data"]["viewer"]["message_threads"]["nodes"]
        # print(thread_data)
        for thread in thread_data:
            if (thread["thread_key"]["thread_fbid"] != None):
                    thread_id_list.append(thread["thread_key"]["thread_fbid"])
                    thread_name_list.append(thread["name"])
        all_thread_data = {
            "threadIDList": thread_id_list,
            "threadNameList": thread_name_list,
            "countThread": len(thread_id_list)
        }
    except Exception as error_log:
        all_thread_data = {
            "error": str(error_log)
        }
    return {
        "dataGet": response_data,
        "ProcessingTime": processing_time,
        "last_seq_id": last_seq_id,
        "dataAllThread": all_thread_data
    }

def get_thread_features(thread_data_get, thread_id, command):
    feature_list = []

    try: thread_data = json.loads(thread_data_get)["o0"]["data"]["viewer"]["message_threads"]["nodes"]
    except: return json.loads(thread_data_get)["o0"]["errors"][0]["summary"]
    for thread_item in thread_data:
        if (str(thread_item["thread_key"]["thread_fbid"]) == str(thread_id)):
            selected_thread = thread_item

    if (selected_thread != None):
        match command:
            case "getAdmin":  # Lấy id Admin Thread
                for admin_data in selected_thread["thread_admins"]:
                        feature_list.append(str(admin_data["id"]))
                export_data = {
                        "adminThreadList": feature_list
                }

            case "threadInfomation": # Lấy thông tin Thread
                thread_info = selected_thread["customization_info"]
                export_data = {
                        "nameThread": selected_thread["name"],
                        "IDThread": thread_id,
                        "emojiThread": thread_info["emoji"],
                        "messageCount": selected_thread["messages_count"],
                        "adminThreadCount": len(selected_thread["thread_admins"]),
                        "memberCount": len(selected_thread["all_participants"]["edges"]),
                        "approvalMode": "Bật" if (selected_thread["approval_mode"] != 0) else "Tắt",
                        "joinableMode": "Bật" if (selected_thread["joinable_mode"]["mode"] != "0") else "Tắt",
                        "urlJoinableThread": selected_thread["joinable_mode"]["link"]
                }
            case "exportMemberListToJson": # Chuyển đổi dữ liệu member Thread
                member_list = selected_thread["all_participants"]["edges"]
                for member in member_list:
                        user_data = member["node"]["messaging_actor"]
                        export_data = json.dumps({
                            user_data["id"]: {
                                "nameFB": str(user_data.get("name")),
                                "idFacebook": str(user_data.get("id")),
                                "profileUrl": str(user_data.get("url")),
                                "avatarUrl": str(user_data["big_image_src"]["uri"]),
                                "gender": str(user_data.get("gender")),
                                "usernameFB": str(user_data.get("username"))
                            }
                        }, skipkeys=True, allow_nan=True, ensure_ascii=False, indent=5)
                        feature_list.append(export_data)
                export_data = feature_list
            case _:
                export_data = {
                        "err": "no data"
                }

        return export_data

    else:
        return "Không lấy được dữ liệu ThreadList, đã xảy ra lỗi T___T"