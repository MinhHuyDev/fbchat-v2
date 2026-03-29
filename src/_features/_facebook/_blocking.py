import requests, json, random
from _core._utils import formAll, mainRequests  

def block_unblock_user(facebook_data, user_id, interaction_choice): # Tương tác Chặn và bỏ chặn người dùng

    # Được lấy dữ liệu và viết vào lúc: 03:12 Thứ 5, ngày 06/07/2023. Tác giả: MinhHuyDev
    """Args:
        user_id: ID of the user to block/unblock (eg. 4) | typeInput: str/int
        interaction_choice: Do you want to block or unblock? (eg. block/unblock) | typeInput: str
    """

    if (interaction_choice == "block"):

        friendly_name = "ProfileCometActionBlockUserMutation"
        doc_id = "6305880099497989"
        variables = json.dumps(
            {
                    "collectionID": None,
                    "hasCollectionAndSectionID": False,
                    "input": {
                        "blocksource": "PROFILE",
                        "should_apply_to_later_created_profiles": False,
                        "user_id": int(user_id),
                        "actor_id": facebook_data["FacebookID"],
                        "client_mutation_id": str(round(random.random() * 1024))
                    },
                    "scale": 3,
                    "sectionID": None,
                    "isPrivacyCheckupContext": False
            }
        )

    elif (interaction_choice == "unblock"):

        friendly_name = "BlockingSettingsBlockMutation"
        doc_id = "6009824239038988"
        variables = json.dumps(
            {
                    "input": {
                        "block_action": "UNBLOCK",
                        "setting": "USER",
                        "target_id": user_id,
                        "actor_id": facebook_data["FacebookID"],
                        "client_mutation_id": "1"
                    },
                    "profile_picture_size": 36
            }
        )

    else:

        return {
            "error": 1,
            "messages": "Không tồn tại lệnh này."
        }

    form_data = formAll(facebook_data, friendly_name, doc_id)
    form_data["variables"] = variables

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)

    if (interaction_choice == "block"):

        if (response.get("data")):
            return {
                    "success": 1,
                    "messages": "Chặn người dùng thành công!"
            }
        else:
            return {
                    "error": 1,
                    "messages": "Chặn người dùng thất bại!"
            }

    elif (interaction_choice == "unblock"):

        if (response.get("data")):
            return {
                    "success": 1,
                    "messages": "Bỏ chặn người dùng thành công!"
            }
        else:
            return {
                    "error": 1,
                    "messages": "Bỏ chặn người dùng thất bại!"
            } 