from unittest.mock import Mock

from _messaging import _createNotes as notes
from _messaging._createNotes import _error_response, _normalize_privacy, _request_error


def test_normalize_privacy():
    assert _normalize_privacy("EVERYONE") == "FRIENDS"
    assert _normalize_privacy("PUBLIC") == "FRIENDS"
    assert _normalize_privacy("FRIENDS") == "FRIENDS"
    assert _normalize_privacy(None) == "FRIENDS"


def test_error_response():
    data = {"errors": [{"message": "Invalid note"}]}
    res = _error_response(data)
    assert res["error"] == 1
    assert res["messages"] == "Invalid note"


def test_request_error():
    res = _request_error("Timeout", Exception("fail"), "Friendly", 123)
    assert len(res["errors"]) == 1
    err = res["errors"][0]
    assert err["message"] == "Timeout"
    assert err["friendly_name"] == "Friendly"
    assert err["doc_id"] == "123"
    assert err["exception"] == "fail"


def test_recreate_note_blocking_uses_only_blocking_operations(monkeypatch):
    delete_note = Mock(return_value={"success": 1, "data": {"id": "old-note"}})
    create_note = Mock(return_value={"success": 1, "data": {"id": "new-note"}})
    monkeypatch.setattr(notes, "_deleteNote_blocking", delete_note)
    monkeypatch.setattr(notes, "_createNote_blocking", create_note)

    result = notes.re_createNote_blocking(
        {"FacebookID": "bot"}, "old-note", "Nội dung mới", privacy="FRIENDS"
    )

    delete_note.assert_called_once_with({"FacebookID": "bot"}, "old-note")
    create_note.assert_called_once_with(
        {"FacebookID": "bot"}, "Nội dung mới", privacy="FRIENDS"
    )
    assert result == {
        "success": 1,
        "messages": "Tạo lại note thành công.",
        "data": {"deleted": {"id": "old-note"}, "created": {"id": "new-note"}},
    }


def test_recreate_note_blocking_stops_when_delete_fails(monkeypatch):
    error = {"error": 1, "messages": "Không thể xoá note."}
    create_note = Mock()
    monkeypatch.setattr(notes, "_deleteNote_blocking", Mock(return_value=error))
    monkeypatch.setattr(notes, "_createNote_blocking", create_note)

    assert notes.re_createNote_blocking({}, "old-note", "Nội dung mới") is error
    create_note.assert_not_called()
