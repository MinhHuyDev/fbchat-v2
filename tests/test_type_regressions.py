from _features._facebook._get_user_info import _parse_response


def test_user_info_treats_non_integer_gender_as_unknown() -> None:
    payload = {
        "payload": {
            "profiles": {
                "42": {
                    "id": "42",
                    "name": "Test User",
                    "gender": "not-an-enum",
                }
            }
        }
    }

    result = _parse_response(payload, "42")

    assert result["genderUser"] == "Unknown (Không xác định)"
