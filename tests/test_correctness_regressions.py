from unittest.mock import AsyncMock, Mock, patch

import pytest

from _features._facebook._archivePost import _parse_result as parse_archive_result
from _features._facebook._deletePost import _parse_result as parse_delete_result
from _features._facebook._unFriend import _parse_result as parse_unfriend_result
from _messaging._listening import listeningEvent

PARSER_CASES = [
    pytest.param(
        parse_unfriend_result,
        {"data": {"friend_remove": {"success": True}}},
        {"data": {"friend_remove": {"success": False}}},
        "Xóa bạn bè thành công!",
        id="unfriend",
    ),
    pytest.param(
        parse_archive_result,
        {"data": {"archive_story": {"success": True}}},
        {"data": {"archive_story": {"success": False}}},
        "Lưu trữ bài viết thành công!",
        id="archive-post",
    ),
    pytest.param(
        parse_delete_result,
        {"data": {"move_to_trash_story": {"success": True}}},
        {"data": {"move_to_trash_story": {"success": False}}},
        "Xóa bài viết thành công!",
        id="delete-post",
    ),
]


@pytest.mark.parametrize(
    ("parser", "success_payload", "false_payload", "success_message"),
    PARSER_CASES,
)
def test_mutation_parser_preserves_success_shape(
    parser, success_payload, false_payload, success_message
):
    assert parser(success_payload) == {"success": 1, "messages": success_message}


@pytest.mark.parametrize(
    ("parser", "success_payload", "false_payload", "success_message"),
    PARSER_CASES,
)
def test_mutation_parser_rejects_null_data(
    parser, success_payload, false_payload, success_message
):
    assert parser({"data": None}) == {
        "error": 1,
        "messages": "Facebook không phản hồi hợp lệ.",
    }


@pytest.mark.parametrize(
    ("parser", "success_payload", "false_payload", "success_message"),
    PARSER_CASES,
)
def test_mutation_parser_rejects_false_success(
    parser, success_payload, false_payload, success_message
):
    assert parser(false_payload) == {
        "error": 1,
        "messages": "Facebook không phản hồi hợp lệ.",
    }


@pytest.mark.parametrize(
    ("parser", "success_payload", "false_payload", "success_message"),
    PARSER_CASES,
)
def test_mutation_parser_rejects_graphql_errors(
    parser, success_payload, false_payload, success_message
):
    payload = {**success_payload, "errors": [{"message": "Mutation failed"}]}

    assert parser(payload) == {"error": 1, "messages": "Mutation failed"}


@pytest.mark.asyncio
async def test_disconnect_delegates_blocking_work_to_thread():
    listener = listeningEvent.__new__(listeningEvent)
    disconnect_blocking = Mock()
    listener.disconnect_blocking = disconnect_blocking

    with patch(
        "_messaging._listening.asyncio.to_thread", new_callable=AsyncMock
    ) as to_thread:
        await listener.disconnect()

    to_thread.assert_awaited_once_with(disconnect_blocking)
    disconnect_blocking.assert_not_called()
