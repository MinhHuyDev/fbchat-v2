import requests, json, random
from _core._utils import parse_cookie_string, formAll, Headers

def create_additional_profile(facebook_data, profile_name, profile_username): # Tạo một trang cá nhân khác trên chinh tài khoản Facebook

    # Được lấy dữ liệu và viết vào lúc: 01:14 Thứ 5, ngày 06/07/2023. Tác giả: MinhHuyDev

    form_data = formAll(facebook_data, "AdditionalProfileCreateMutation", 4699419010168408)
    form_data["variables"] = json.dumps(
        {
            "input": {
                    "name": profile_name,
                    "source": "PROFILE_SWITCHER",
                    "user_name": profile_username,
                    "actor_id": facebook_data["FacebookID"],
                    "client_mutation_id": str(round(random.random() * 1024))
            }
        }
    )

    request_params = {
        "headers": Headers(facebook_data["cookieFacebook"], form_data),
        "timeout": 60000,
        "url": "https://www.facebook.com/api/graphql/",
        "data": form_data,
        "cookies": parse_cookie_string(facebook_data["cookieFacebook"]),
        "verify": True
    }

    response = json.loads(requests.post(**request_params).text)

    if (response.get("data")):
        if (response.get("data").get("additional_profile_create").get("error_message")):
            return {
                    "error": 1,
                    "message": response["data"]["additional_profile_create"]["error_message"]
            }
        else:
            return {
                    "success": 1,
                    "messages": "Tạo trang cá nhân khác trên tài khoản Facebook thành công!"
            }
    else:
        return {
            "error": 1,
            "messages": response["errors"][0]["message"]
        }
