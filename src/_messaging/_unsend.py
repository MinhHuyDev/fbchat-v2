import requests, json
from _core._utils import formAll, mainRequests
 
def unsend_message(message_id, facebook_data):

     form_data = formAll(facebook_data, requireGraphql=False)
     form_data["message_id"] = message_id

     response = json.loads(requests.post(**mainRequests("https://www.facebook.com/messaging/unsend_message/", form_data, facebook_data["cookieFacebook"])).text.split("for (;;);")[1])

     if (response.get("error")):
          return Exception({"error": str(response)})
     return {
          "success": 1,
          "messages": "Thu hồi tin nhắn thành công."
     }

# completed at 09:36 30/06/2023 | last updated at 19:50 13/12/2023
