import requests, json, random
from _core._utils import formAll, mainRequests

def change_bio(facebook_data, new_bio_content, create_post=False): # Thay đổi Bio trên trang Facebook

    # Được lấy dữ liệu và viết vào lúc: 09:10 Thứ 4, ngày 05/07/2023. Tác giả: MinhHuyDev
    """Args:
        new_bio_content: new content bio FB (eg. MinhHuyDev) | typeInput: str
        create_post: Create an post about this change (eg. True/False) | typeInput: bool
    """

    form_data = formAll(facebook_data, "ProfileCometSetBioMutation", 6293552847364844)
    form_data["variables"] = json.dumps(
        {
            "input": {
                    "bio": str(new_bio_content),
                    "publish_bio_feed_story": create_post,
                    "actor_id": facebook_data["FacebookID"],
                    "client_mutation_id": str(round(random.random() * 1024))
            },
            "hasProfileTileViewID": False,
            "profileTileViewID": None,
            "scale": 1
        }
    )

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)

    if (response.get("data")):
        check_bio_result = response.get("data").get("profile_intro_card_set").get("profile_intro_card").get("bio")
        if (check_bio_result.get("text") == new_bio_content):
            return {
                    "success": 1,
                    "messages": "Thay đổi bio của bạn thành công!!"
            }
        else:
            return {
                    "error": 1,
                    "description": "??"
            }
    else:
        return {
            "error": 1
        }
        