import json, requests, time, json, random
from _core._utils import formAll, mainRequests

def create_post(facebook_data, post_content, attachment_id=None): # Tạo bài viết trên Facebook

    # Được lấy dữ liệu và viết vào lúc: 09:40 Thứ 4, ngày 05/07/2023. Tác giả: MinhHuyDev
    """Args:
        post_content: content of post to create (eg. MinhHuy create new post!) | typeInput: str
        attachment_id: Coming soon....
    """

    form_data = formAll(facebook_data, "ComposerStoryCreateMutation", 6534257523262244)
    form_data["variables"] = json.dumps(
        {
            "input": {
                    "composer_entry_point": "inline_composer",
                    "composer_source_surface": "timeline",
                    "source": "WWW",
                    "attachments": [],
                    "audience": {
                        "privacy": {
                            "allow": [],
                            "base_state": "EVERYONE",
                            "deny": [],
                            "tag_expansion_state": "UNSPECIFIED"
                        }
                    },
                    "message": {
                        "ranges": [],
                        "text": post_content
                    },
                    "with_tags_ids": [],
                    "inline_activities": [],
                    "explicit_place_id": "0",
                    "text_format_preset_id": "0",
                    "logging": {
                        "composer_session_id": facebook_data["sessionID"]
                    },
                    "navigation_data": {
                        "attribution_id_v2": f"ProfileCometTimelineListViewRoot.react,comet.profile.timeline.list,tap_bookmark,{int(time.time() * 1000)},{facebook_data['jazoest']},{facebook_data['FacebookID']}"
                    },
                    "tracking": "[null]",
                    "actor_id": facebook_data["FacebookID"],
                    "client_mutation_id": "1"
            },
            "displayCommentsFeedbackContext": None,
            "displayCommentsContextEnableComment": None,
            "displayCommentsContextIsAdPreview": None,
            "displayCommentsContextIsAggregatedShare": None,
            "displayCommentsContextIsStorySet": None,
            "feedLocation":"TIMELINE",
            "focusCommentID": None,
            "scale": str(round(random.random() * 1024)),
            "privacySelectorRenderLocation":"COMET_STREAM",
            "renderLocation":"timeline",
            "useDefaultActor": False,
            "inviteShortLinkKey": None,
            "isFeed": False,
            "isFundraiser": False,
            "isFunFactPost": False,
            "isGroup": False,
            "isEvent": False,
            "isTimeline": True,
            "isSocialLearning":False,
            "isPageNewsFeed": False,
            "isProfileReviews": False,
            "isWorkSharedDraft": False,
            "UFI2CommentsProvider_commentsKey":"ProfileCometTimelineRoute",
            "hashtag": None,
            "canUserManageOffers": False,
            "__relay_internal__pv__IsWorkUserrelayprovider": False,
            "__relay_internal__pv__IsMergQAPollsrelayprovider": False,
            "__relay_internal__pv__StoriesArmadilloReplyEnabledrelayprovider": False,
            "__relay_internal__pv__StoriesRingrelayprovider":False
        }
    )

    response = json.loads(requests.post(**mainRequests("https://www.facebook.com/api/graphql/", form_data, facebook_data["cookieFacebook"])).text)

    if (response.get("data")):
        return {
            "success": 1,
            "messages": "Tạo bài viết thành công!",
            "urlPost": response["data"]["story_create"]["story"]["url"]
        }
    else:
        return {
            "error": 1,
            "messages": response["errors"][0]["message"]
        }
