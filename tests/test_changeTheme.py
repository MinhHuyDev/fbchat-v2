from unittest.mock import Mock

import pytest

from _messaging import _changeTheme as themes
from _messaging._changeTheme import (
    _graphql_error_response,
    _normalize_theme,
    _request_error,
)


def test_request_error():
    res = _request_error("Timeout", Exception("fail"), "Friendly", 123)
    assert len(res["errors"]) == 1
    err = res["errors"][0]
    assert err["message"] == "Timeout"
    assert err["friendly_name"] == "Friendly"
    assert err["doc_id"] == "123"
    assert err["exception"] == "fail"


def test_graphql_error_response():
    data = {"errors": [{"message": "Invalid query"}]}
    res = _graphql_error_response(data)
    assert res["error"] == 1
    assert res["messages"] == "Invalid query"


def test_normalize_theme():
    raw_data = {
        "id": "999",
        "accessibility_label": "Dark Mode",
        "app_color_mode": "DARK",
    }
    normalized = _normalize_theme(raw_data)
    assert normalized is not None
    assert normalized["id"] == "999"
    assert normalized["name"] == "Dark Mode"
    assert normalized["appColorMode"] == "DARK"


def test_normalize_theme_empty():
    assert _normalize_theme({}) is None
    assert _normalize_theme({"no_id": 1}) is None


def test_find_theme_blocking_uses_blocking_theme_list(monkeypatch):
    list_themes = Mock(
        return_value={
            "success": 1,
            "data": [{"id": "999", "name": "Dark Mode"}],
        }
    )
    monkeypatch.setattr(themes, "_listThemes_blocking", list_themes)

    result = themes._findTheme_blocking({}, "dark mode")

    list_themes.assert_called_once_with({})
    assert result["success"] == 1
    assert result["data"] == {"id": "999", "name": "Dark Mode"}


def test_change_theme_blocking_uses_blocking_theme_lookup(monkeypatch):
    find_theme = Mock(
        return_value={"success": 1, "data": {"id": "999", "name": "Dark Mode"}}
    )
    publish = Mock(return_value={"success": 1, "payload": {"request_id": 1}})
    monkeypatch.setattr(themes, "_findTheme_blocking", find_theme)
    monkeypatch.setattr(themes, "_publish_ls_requests", publish)

    data_fb = {"FacebookID": "bot"}
    result = themes._changeTheme_blocking(data_fb, "thread", "Dark Mode")

    find_theme.assert_called_once_with(data_fb, "Dark Mode")
    publish.assert_called_once()
    assert result["success"] == 1
    assert result["data"]["themeID"] == "999"


@pytest.mark.asyncio
async def test_func_normalizes_missing_optional_arguments_before_delegating():
    result = await themes.func({"FacebookID": "bot"})

    assert result["error"] == 1
    assert result["messages"] == "threadID is required."
