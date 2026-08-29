from __future__ import annotations

from importlib.metadata import version

import fbchat_v2
from fbchat_v2._features._facebook import _unFriend
from fbchat_v2._features._thread import _all_thread_data
from fbchat_v2._messaging._listening import listeningEvent


def test_public_namespace_and_version_are_stable() -> None:
    assert fbchat_v2.__version__ == version("fbchat-v2") == "2.3.0"
    assert callable(_unFriend.func)


def test_blocking_sequence_refresh_never_calls_async_transport(monkeypatch) -> None:
    listener = listeningEvent({"cookieFacebook": "test"})

    def fail_async(*args, **kwargs):
        raise AssertionError("blocking API called the async transport")

    monkeypatch.setattr(_all_thread_data, "func", fail_async)
    monkeypatch.setattr(
        _all_thread_data,
        "func_blocking",
        lambda data_fb: {"last_seq_id": 42},
    )

    assert listener.get_last_seq_id_blocking() == 42
    assert listener.fbt == {"last_seq_id": 42}
