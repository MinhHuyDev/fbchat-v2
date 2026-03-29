import requests, json, random
from _core._utils import formAll, mainRequests

def toggle_professional_mode(facebook_data, professional_mode_status=None): # Bật chế độ chuyên nghiệp Trang cá nhân

    # Được lấy dữ liệu và viết vào lúc: 01:03 Thứ 5, ngày 06/07/2023. Tác giả: MinhHuyDev
    """Args:
        professional_mode_status: Do you want it on or off? (eg. True/False) | typeInput: bool
    """

    if ((professional_mode_status.lower() == "on") | (professional_mode_status.lower() == "bật") | (professional_mode_status == True)):
        doc_id = "6580386111988379"
        friendly_name = "CometProfilePlusOnboardingDialogTransitionMutation"
        variables = json.dumps(
            {
                    "category_id": int(random.random() * 1738263827237839),
                    "surface": None
            }
        )
    elif ((professional_mode_status.lower() == "off") | (professional_mode_status.lower() == "tắt") | (professional_mode_status == False)):
        doc_id = "4947853815250139"
        friendly_name = "CometProfilePlusRollbackMutation"
        variables = json.dumps({})
    else:
        return {
            "error": -1,
            "messages": "Không có sự lựa chọn được đưa ra."
        }

    form_data = formAll(facebook_data, friendly_name, doc_id)
    form_data["variables"] = variables


    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)

    if (response.get("data")):
        return {
            "success": 1,
            "messages": "Bật trang cá nhân chuyên nghiệp thành công!" if ((professional_mode_status.lower() == "on") | (professional_mode_status.lower() == "bật")) else "Tắt trang cá nhân chuyên nghiệp thành công!",
        }
    else:
        return {
            "error": 1,
            "message": response["errors"][0]["message"]
        }
