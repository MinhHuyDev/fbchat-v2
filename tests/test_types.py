from _core._types import ErrorResponse, LoginSuccessPayload, SuccessResponse


def test_typed_dict_optional_keys_do_not_require_python_311_not_required():
    assert SuccessResponse.__required_keys__ == frozenset({"success"})
    assert SuccessResponse.__optional_keys__ == frozenset(
        {"payload", "messages", "data"}
    )
    assert ErrorResponse.__required_keys__ == frozenset({"error"})
    assert ErrorResponse.__optional_keys__ == frozenset({"payload", "messages"})
    assert LoginSuccessPayload.__required_keys__ == frozenset(
        {"setCookies", "accessTokenFB"}
    )
    assert LoginSuccessPayload.__optional_keys__ == frozenset({"cookiesKeyValueList"})
