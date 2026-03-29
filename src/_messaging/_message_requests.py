import requests, json
from _core._utils import formAll, mainRequests

def get_pending_messages(facebook_data): # Lấy danh sách tin nhắn chờ

          # Được lấy dữ liệu và viết vào lúc: 21:43 Thứ 4, ngày 05/07/2023. Tác giả: MinhHuyDev
          # DATETIME - UPDATE: 13/02/2024 13:21

          form_data = formAll(facebook_data, requireGraphql=0)
          form_data["queries"] = json.dumps({
               "o0": {
                    "doc_id": "3336396659757871",
                    "query_params": {
                         "limit": 10000,
                         "before": None,
                         "tags": ["PENDING"], # INBOX, PENDING, ARCHIVED
                         "includeDeliveryReceipts": False,
                         "includeSeqID": True,
                    }
               }
          })

          response = requests.post(**mainRequests("https://www.facebook.com/api/graphqlbatch/", form_data, facebook_data["cookieFacebook"]))
          # return response.text.split("{\"successful_results\"")[0]
          response_data = json.loads(response.text.split('{"successful_results"')[0])
          pending_list = response_data['o0']['data']['viewer']['message_threads']['nodes']
          export_data_dict = {"data":{}}
          total = 0
          for pending_item in pending_list:
               message_nodes = pending_item['last_message']['nodes']
               try:
                    content_message, sender_id, timestamp_precise = message_nodes[0]['snippet'], message_nodes[0]['message_sender']['messaging_actor']['id'], message_nodes[0]['timestamp_precise']
                    export_data_dict[total] = {'senderID': sender_id, 'snippet': content_message, 'timestamp_precise': timestamp_precise}
                    total += 1
               except:
                    pass
          export_data_dict['total_count'] = total
          return {
               "success": 1,
               "messageRequests": json.dumps(export_data_dict, indent=5)
          }