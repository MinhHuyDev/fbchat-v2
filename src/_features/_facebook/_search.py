import requests, json, random
from _core._utils import formAll, mainRequests, randStr

def search_facebook(facebook_data, search_keyword): # Tìm kiếm trên Facebook

    # Được lấy dữ liệu và viết vào lúc: 01:42 Thứ 5, ngày 06/07/2023. Tác giả: MinhHuyDev
    """Args:
        search_keyword: Content to search for on FB (eg. Mark Zuckerberg) | typeInput: str
    """

    form_data = formAll(facebook_data, "SearchCometResultsInitialResultsQuery", 6866854183333610)
    form_data["variables"] = json.dumps(
        {
            "count": 5,
            "allow_streaming": False,
            "args": {
                    "callsite": "COMET_GLOBAL_SEARCH",
                    "config": {
                        "exact_match": False,
                        "high_confidence_config": None,
                        "intercept_config": None,
                        "sts_disambiguation": None,
                        "watch_config":None
                    },
                    "context": {
                        "bsid": str(randStr(8) + "-" + randStr(4) + "-" + randStr(4) + "-" + randStr(4) + "-" + randStr(12)),
                        "tsid": str(random.random())
                    },
                    "experience": {
                        "encoded_server_defined_params": None,
                        "fbid": None,
                        "type": "GLOBAL_SEARCH"
                    },
                    "filters": [],
                    "text": str(search_keyword)
            },
            "cursor": None,
            "feedbackSource": 23,
            "fetch_filters": True,
            "renderLocation": "search_results_page",
            "scale": 3,
            "stream_initial_count": 0,
            "useDefaultActor": False,
            "__relay_internal__pv__SearchCometResultsShowUserAvailabilityrelayprovider": True,
            "__relay_internal__pv__IsWorkUserrelayprovider": False,
            "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
            "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": False,
            "__relay_internal__pv__StoriesRingrelayprovider": False
        }
    )

    search_results_list = []
    search_results_dict = []


    try:
        response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)
        search_data = response["data"]["serpResponse"]["results"]["edges"][0]["relay_rendering_strategy"]["result_rendering_strategies"]
        for result_data in search_data:
            search_results_dict.append({
                "name": result_data["view_model"]["profile"]["name"],
                "id": result_data["view_model"]["profile"]["id"],
                "url": result_data["view_model"]["profile"]["url"]
            })
            search_results_list.append("🔮Tên người dùng: " + result_data["view_model"]["profile"]["name"] + "\n⚗️ID người dùng: " + result_data["view_model"]["profile"]["id"] + "\n🏷️Liên kết trang cá nhân: " + result_data["view_model"]["profile"]["url"] + "\n≈ ≈ ≈ ≈ ≈ ≈ ≈ ≈")
        return {
            "success": 1,
            "searchResults": "≈ ≈ ≈ Tìm Kiếm Facebook ≈ ≈ ≈\n\n" + "\n".join(search_results_list) + "\n🔎Từ khoá tìm kiếm: " + str(search_keyword) + "\n📊Số lượng kết quả: 5",
            "searchResultsDict": search_results_dict
        }
    except Exception as error_log:
        return {
            "error": 1,
            "messages": "ERR: " + str(error_log)
        }