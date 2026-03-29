import requests, json
from _core._utils import formAll, mainRequests

def get_notifications(facebook_data): # Lấy thông báo Facebook

    # Được lấy dữ liệu và viết vào lúc: 02:32 Thứ 5, ngày 06/07/2023. Tác giả: MinhHuyDev

    form_data = formAll(facebook_data, "CometNotificationsDropdownQuery", 6770067089747450)
    form_data["variables"] = json.dumps(
        {
            "count":15,
            "environment":"MAIN_SURFACE",
            "scale":3
        }
    )

    notification_results_list = []

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)

    try:
        notification_data = response["data"]["viewer"]["notifications_page"]["edges"]
        for notification_item, count in zip(notification_data, range(1, len(notification_data) + 1)):
            try:
                    notification_results_list.append(str(count) + "." + notification_item["node"]["notif"]["body"]["text"])
            except:
                    pass
    except Exception as error_log:
        return {
            "error": 1,
            "messages": "ERR: " + str(error_log)
        }
    return {
        "success": 1,
        "NotificationResults": notification_results_list
    }
