import random, attr, requests, json
# import __facebookToolsV2
from _core._utils import str_base,  get_files_from_paths

def upload_attachment(file_path, facebook_data):


     USER_AGENTS = ["Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_3) AppleWebKit/601.1.10 (KHTML, like Gecko) Version/8.0.5 Safari/601.1.10", "Mozilla/5.0 (Windows NT 6.3; WOW64; ; NCT50_AAP285C84A1328) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.90 Safari/537.36", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1", "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6"]

     headers = {
          "Referer": "https://www.facebook.com",
          "Accept": "text/html",
          "User-Agent": random.choice(USER_AGENTS),
          "Cookie": facebook_data["cookieFacebook"],
     }

     files = get_files_from_paths(file_path)
     request_counter = attr.ib(0).counter
     request_counter += 1
     form_data = {}
     form_data["voice_clip"] = False
     form_data["__a"] = 1
     form_data["__req"] = str_base(request_counter, 36)
     form_data["fb_dtsg"] = facebook_data["fb_dtsg"]

     file_dict = {
          "upload_{}".format(index): file_data for index, file_data in enumerate(files)
     }

     upload_response = requests.post("https://upload.facebook.com/ajax/mercury/upload.php", headers=headers, data=form_data, files=file_dict).text

     try:
          upload_response = json.loads(upload_response.replace("for (;;);", ""))["payload"]
     except:
          return print("ERROR-UPLOADED: " + str(upload_response))
     attachment_data_list = []
     try:
          for attachment_data in upload_response["metadata"][0].values():
               attachment_data_list.append(attachment_data)
     except:
          for attachment_data in upload_response["metadata"]['0'].values():
               attachment_data_list.append(attachment_data)
     try: attachment_url = attachment_data_list[3]
     except: attachment_url = None
     return {
          "attachmentID": attachment_data_list[0],
          "attachmentUrl": attachment_url,
          "attachmentType": attachment_data_list[2],
          "attachmentDataSend": None# resultData
     }


# _uploadAttachment("file-name.jpg", dataFB)
# print(_uploadAttachment("Name file to need uploads", __facebookToolsV2.dataGetHome("this is cookie Facebook")))
# output-image: {'attachmentID': 676421537934928, 'attachmentUrl': 'https://scontent.fsgn5-8.fna.fbcdn.net/v/t1.15752-9/328999258_555852780015611_2452318447980968642_n.jpg?_nc_cat=109&ccb=1-7&_nc_sid=b65b05&_nc_ohc=ngkZ0e3NqzYAX8ZdVYx&_nc_ht=scontent.fsgn5-8.fna&oh=03_AdTrTWSDqWiSrYcTG8c_WKn1ksUdttUbcK3hmvTu2WEmRQ&oe=65A10D97', 'attachmentType': 'image/jpeg', 'attachmentDataSend': [(676421537934928, 'image/jpeg')]}
# ouput-video: {'attachmentID': 848156417052481, 'attachmentUrl': 'https://scontent.fsgn5-10.fna.fbcdn.net/v/t15.3394-10/416827059_6699338906842547_1263326403482126710_n.jpg?_nc_cat=107&ccb=1-7&_nc_sid=407108&_nc_eui2=AeGD75e6KV6vQfPcP4aCq9Yua-QBDRBkDOJr5AENEGQM4oV21IQSIev2_QwXWrdXFSg&_nc_ohc=aFezV-zIf3EAX_UjIAF&_nc_ht=scontent.fsgn5-10.fna&oh=03_AdQESAAFJ9GODQx-H36DmwWZ_ENQvbqnWz5Mm6lcZmoc8Q&oe=6599A974', 'attachmentType': 'video/mp4', 'attachmentDataSend': None}

# completed at 14:03 19/06/2023 | last updated at 12:03 AM 10/03/2026
