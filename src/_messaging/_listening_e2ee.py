"""
fbchat-v2 :: _listening_e2ee.py
================================

Lắng nghe tin nhắn Facebook Messenger có giải mã E2EE (Secret Conversations /
Labyrinth) bằng cách giao tiếp với binary Go `fbchat-bridge-e2ee` qua
stdin/stdout (line-delimited JSON-RPC).

Ưu điểm so với phiên bản ctypes/dll:
- Không cần thư mục `meta-messenger.js/` tồn tại trong workspace.
- Không cần load shared library bằng ctypes (an toàn hơn — bridge crash không
  kéo Python crash theo).
- Bridge có thể được phân phối dưới dạng .exe đơn lẻ.

Cách build binary (1 lần):
    cd fbchat-v2/bridge-e2ee
    git clone https://github.com/mautrix/meta.git ./meta
    go mod tidy
    go build -ldflags="-s -w" -o ../build/fbchat-bridge-e2ee.exe .

Override đường dẫn binary bằng env: FBCHAT_E2EE_BIN=/path/to/binary

Tại sao không pure Python?
--------------------------
Giải mã E2EE Messenger cần Signal Protocol (Curve25519, Double Ratchet, Sender
Keys, AES-GCM, HKDF, Noise XX) + giao thức nội bộ Meta (Labyrinth /
Lightspeed). Tổng cộng ~100k LOC Go đã được audit, không có lib Python tương
đương. Tự re-implement = rủi ro bảo mật cao + bảo trì không nổi khi Meta đổi
giao thức.

Author: MinhHuyDev
"""

from __future__ import annotations

import asyncio
import datetime
import hashlib
import hmac
import itertools
import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable, Optional
from urllib.parse import unquote, urlparse

import httpx

from _core import __version__ as _PACKAGE_VERSION
from _core._utils import parse_cookie_string
from _messaging._bridge_checksums import BRIDGE_RELEASE_VERSION, BRIDGE_SHA256

# ---------------------------------------------------------------------------
# Binary discovery
# ---------------------------------------------------------------------------


_MAX_BRIDGE_SIZE = 200 * 1024 * 1024
_RELEASE_VERSION_PATTERN = re.compile(r"[0-9A-Za-z][0-9A-Za-z._+-]*")
_TRUSTED_DOWNLOAD_HOSTS = {
    "api.github.com",
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
}


def _binary_name() -> str:
    name = (
        "fbchat-bridge-e2ee.exe"
        if sys.platform.startswith("win")
        else "fbchat-bridge-e2ee"
    )
    return name


def _default_binary_path() -> Path:
    name = _binary_name()
    here = Path(__file__).resolve()
    project_root = here.parents[2]
    if _is_source_checkout():
        return project_root / "build" / name

    if sys.platform.startswith("win"):
        cache_root = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    else:
        cache_root = Path(os.environ.get("XDG_CACHE_HOME") or (Path.home() / ".cache"))
    return cache_root / "fbchat-v2" / "bridge" / f"v{_PACKAGE_VERSION}" / name


def _is_source_checkout() -> bool:
    return (Path(__file__).resolve().parents[2] / "pyproject.toml").is_file()


def _release_version_and_digest(binary_name: str) -> tuple[str, str]:
    release_version = BRIDGE_RELEASE_VERSION or _PACKAGE_VERSION
    if not _RELEASE_VERSION_PATTERN.fullmatch(release_version):
        raise RuntimeError("Phiên bản package không hợp lệ để tải bridge an toàn.")
    if BRIDGE_RELEASE_VERSION and BRIDGE_RELEASE_VERSION != _PACKAGE_VERSION:
        raise RuntimeError(
            "Bảng checksum bridge không khớp phiên bản package đang cài đặt."
        )

    expected_sha256 = (
        (os.environ.get("FBCHAT_E2EE_SHA256") or BRIDGE_SHA256.get(binary_name) or "")
        .strip()
        .lower()
    )
    if expected_sha256.startswith("sha256:"):
        expected_sha256 = expected_sha256.partition(":")[2]
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise RuntimeError(
            "Thiếu checksum SHA-256 tin cậy cho bridge. Hãy tự build, đặt "
            "FBCHAT_E2EE_BIN hoặc cung cấp FBCHAT_E2EE_SHA256 từ nguồn độc lập."
        )
    return release_version, expected_sha256


def _validate_https_download_url(url: str) -> None:
    parsed_url = urlparse(url)
    hostname = (parsed_url.hostname or "").lower()
    try:
        port = parsed_url.port
    except ValueError as error:
        raise RuntimeError("Release trả về URL tải bridge không hợp lệ.") from error
    if (
        parsed_url.scheme != "https"
        or hostname not in _TRUSTED_DOWNLOAD_HOSTS
        or port not in (None, 443)
        or parsed_url.username is not None
        or parsed_url.password is not None
    ):
        raise RuntimeError("Release trả về URL tải bridge không hợp lệ.")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    total = 0
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(64 * 1024), b""):
            total += len(chunk)
            if total > _MAX_BRIDGE_SIZE:
                raise RuntimeError("Bridge vượt quá giới hạn 200 MiB.")
            digest.update(chunk)
    if total == 0:
        raise RuntimeError("Bridge rỗng.")
    return digest.hexdigest()


def _platform_bridge_asset() -> tuple[str, str]:
    import platform

    system = platform.system().lower()
    machine = platform.machine().lower()
    if system not in {"darwin", "linux", "windows"}:
        raise RuntimeError(f"Hệ điều hành không được hỗ trợ để tự động tải: {system}")
    architecture = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "arm64": "arm64",
        "aarch64": "arm64",
    }.get(machine)
    if architecture is None:
        raise RuntimeError(f"Kiến trúc không được hỗ trợ để tự động tải: {machine}")
    if system == "windows" and architecture == "arm64":
        raise RuntimeError("Windows ARM64 không có sẵn prebuilt binary. Hãy tự build.")

    goos = system
    goarch = architecture
    binary_name = f"fbchat-bridge-e2ee-{goos}-{goarch}"
    if goos == "windows":
        binary_name += ".exe"
    return binary_name, goos


def _verify_managed_binary(path: Path) -> None:
    import stat

    binary_name, _ = _platform_bridge_asset()
    _, expected_sha256 = _release_version_and_digest(binary_name)
    if not hmac.compare_digest(_sha256_file(path), expected_sha256):
        raise RuntimeError("Checksum SHA-256 của bridge cache không khớp package.")
    if os.name != "nt":
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)


def _download_bridge(target_path: Path) -> None:
    import logging
    import stat

    logger = logging.getLogger("fbchat")
    binary_name, goos = _platform_bridge_asset()
    release_version, expected_sha256 = _release_version_and_digest(binary_name)

    logger.info(
        "Đang tải bridge E2EE %s từ release v%s...",
        binary_name,
        release_version,
    )

    release_tag = f"v{release_version}"
    api_url = (
        "https://api.github.com/repos/MinhHuyDev/fbchat-v2/releases/tags/"
        f"{release_tag}"
    )
    temporary_path: Path | None = None
    try:
        resp = httpx.get(api_url, timeout=10, follow_redirects=True)
        resp.raise_for_status()
        for redirect in [*getattr(resp, "history", []), resp]:
            _validate_https_download_url(str(redirect.url))
        release_payload = resp.json()
        if release_payload.get("tag_name") != release_tag:
            raise RuntimeError("GitHub API trả về release tag không khớp package.")
        assets = release_payload.get("assets", [])
        download_url = None
        github_digest = None
        for asset in assets:
            if isinstance(asset, dict) and asset.get("name") == binary_name:
                download_url = asset.get("browser_download_url")
                github_digest = asset.get("digest")
                break

        if not download_url:
            raise RuntimeError(
                f"Không tìm thấy {binary_name} trên release {release_tag}."
            )

        parsed_url = urlparse(download_url)
        _validate_https_download_url(download_url)
        if (parsed_url.hostname or "").lower() != "github.com":
            raise RuntimeError("GitHub API trả về asset URL không chính thức.")
        expected_path = (
            f"/MinhHuyDev/fbchat-v2/releases/download/{release_tag}/{binary_name}"
        )
        if unquote(parsed_url.path) != expected_path:
            raise RuntimeError("GitHub API trả về asset ngoài release đã pin.")
        if github_digest:
            github_sha256 = str(github_digest).lower().removeprefix("sha256:")
            if not hmac.compare_digest(github_sha256, expected_sha256):
                raise RuntimeError(
                    "Digest trên GitHub Release không khớp checksum trong package."
                )

        target_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if os.name != "nt":
            os.chmod(target_path.parent, 0o700)

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{target_path.name}.",
            suffix=".download",
            dir=target_path.parent,
        )
        os.close(descriptor)
        temporary_path = Path(temporary_name)

        digest = hashlib.sha256()
        downloaded = 0
        with httpx.stream(
            "GET", download_url, timeout=60, follow_redirects=True
        ) as response:
            response.raise_for_status()
            for redirect in [*response.history, response]:
                _validate_https_download_url(str(redirect.url))
            try:
                declared_size = int(response.headers.get("content-length", "0") or 0)
            except (TypeError, ValueError) as error:
                raise RuntimeError("Content-Length của bridge không hợp lệ.") from error
            if declared_size < 0 or declared_size > _MAX_BRIDGE_SIZE:
                raise RuntimeError("Bridge vượt quá giới hạn tải 200 MiB.")
            with temporary_path.open("wb") as file_handle:
                for chunk in response.iter_bytes(chunk_size=64 * 1024):
                    downloaded += len(chunk)
                    if downloaded > _MAX_BRIDGE_SIZE:
                        raise RuntimeError("Bridge vượt quá giới hạn tải 200 MiB.")
                    digest.update(chunk)
                    file_handle.write(chunk)
                file_handle.flush()
                os.fsync(file_handle.fileno())

        if downloaded == 0:
            raise RuntimeError("Bridge tải về rỗng.")
        if declared_size and downloaded != declared_size:
            raise RuntimeError("Kích thước bridge tải về không khớp Content-Length.")
        if not hmac.compare_digest(digest.hexdigest(), expected_sha256):
            raise RuntimeError("Checksum SHA-256 của bridge không khớp package.")

        if goos != "windows":
            os.chmod(temporary_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        temporary_path.replace(target_path)
        if os.name != "nt":
            directory_fd = os.open(target_path.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)

        logger.info(f"Đã tải thành công bridge E2EE vào {target_path}")
    except Exception as error:
        raise RuntimeError(f"Lỗi khi tải tự động bridge E2EE: {error}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _resolve_binary() -> Path:
    override = os.environ.get("FBCHAT_E2EE_BIN")
    candidate = Path(override) if override else _default_binary_path()
    if candidate.exists() and not override and not _is_source_checkout():
        try:
            _verify_managed_binary(candidate)
        except Exception as error:
            import logging

            logging.getLogger("fbchat").warning(
                "Bridge cache không hợp lệ, sẽ tải lại: %s", error
            )
            candidate.unlink()
    if not candidate.exists():
        if override:
            raise FileNotFoundError(
                f"Không tìm thấy bridge binary tại {candidate} (do FBCHAT_E2EE_BIN chỉ định)."
            )
        import logging

        logger = logging.getLogger("fbchat")
        logger.info(f"Không tìm thấy bridge tại {candidate}, tiến hành tải tự động...")
        try:
            _download_bridge(candidate)
        except Exception as e:
            raise FileNotFoundError(
                f"{e}\n"
                f"Vui lòng tự build: cd fbchat-v2/bridge-e2ee && go build -o ../build/{candidate.name} .\n"
                "Hoặc đặt FBCHAT_E2EE_BIN; source checkout chỉ tự tải khi có "
                "FBCHAT_E2EE_SHA256 tin cậy."
            ) from e
    return candidate


# ---------------------------------------------------------------------------
# Subprocess RPC client
# ---------------------------------------------------------------------------


class BridgeError(RuntimeError):
    """Bridge trả về `ok:false` hoặc lỗi truyền tải."""


class _BridgeProcess:
    """RPC client cho fbchat-bridge-e2ee.

    - Một luồng đọc stdout, phân phối response theo `id` về caller hoặc đẩy
      event vào `events` queue.
    - `call(method, params)` block tới khi nhận response.
    - Watchdog thread giám sát subprocess health, auto-respawn khi crash.
    """

    MAX_RETRIES: int = 5
    BASE_BACKOFF: float = 2.0  # seconds — exponential: 2, 4, 8, 16, 32
    MAX_RPC_REQUEST_BYTES: int = 150 * 1024 * 1024

    def __init__(self, binary: Path, *, log_stderr: bool = False) -> None:
        self.events: "Queue[dict[str, Any]]" = Queue()
        self._next_id = itertools.count(1)
        self._pending: dict[int, Queue] = {}
        self._lock = threading.Lock()
        self._write_lock = threading.Lock()
        self._closed = False
        self._stop_event = threading.Event()
        self._binary = binary
        self._log_stderr = log_stderr

        self._spawn()

    def _spawn(self) -> None:
        """Spawn subprocess và khởi động reader/stderr threads."""
        self._closed = False
        self._proc = subprocess.Popen(
            [str(self._binary)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

        # Luôn drain stderr để bridge không bị deadlock khi pipe đầy. Việc in
        # nội dung là opt-in vì diagnostic có thể chứa dữ liệu riêng tư.
        self._stderr_thread = threading.Thread(target=self._drain_stderr, daemon=True)
        self._stderr_thread.start()

    # ------------------------------------------------------------------
    def _drain_stderr(self) -> None:
        assert self._proc.stderr is not None
        for raw in self._proc.stderr:
            try:
                line = raw.decode("utf-8", errors="replace").rstrip()
            except Exception:  # noqa: BLE001
                continue
            if self._log_stderr:
                print(f"[bridge stderr] {line}", file=sys.stderr)

    def _read_loop(self) -> None:
        assert self._proc.stdout is not None
        for raw in self._proc.stdout:
            if not raw:
                continue
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError as exc:
                detail = f"{exc} :: {raw!r}" if self._log_stderr else "details hidden"
                print(
                    f"[bridge] bad json ({len(raw)} bytes): {detail}", file=sys.stderr
                )
                continue

            if "event" in msg:
                self.events.put(msg["event"])
                continue

            mid = msg.get("id")
            with self._lock:
                q = self._pending.pop(mid, None)
            if q is not None:
                q.put(msg)

        self._closed = True
        with self._lock:
            for q in self._pending.values():
                q.put({"ok": False, "error": "bridge exited"})
            self._pending.clear()
        self.events.put({"type": "closed"})

    # ------------------------------------------------------------------
    def call_blocking(
        self, method: str, params: Optional[dict] = None, timeout: float = 60.0
    ) -> dict[str, Any]:
        if self._closed or self._proc.poll() is not None:
            raise BridgeError("bridge process is not running")

        rid = next(self._next_id)
        q: Queue = Queue(maxsize=1)
        with self._lock:
            self._pending[rid] = q

        payload = {"id": rid, "method": method, "params": params or {}}
        line = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
        if len(line) > self.MAX_RPC_REQUEST_BYTES:
            with self._lock:
                self._pending.pop(rid, None)
            raise BridgeError(f"{method}: request exceeds the 150 MiB JSON-RPC limit")
        assert self._proc.stdin is not None
        try:
            with self._write_lock:
                self._proc.stdin.write(line)
                self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            with self._lock:
                self._pending.pop(rid, None)
            raise BridgeError(f"write failed: {exc}") from exc

        try:
            resp = q.get(timeout=timeout)
        except Empty:
            with self._lock:
                self._pending.pop(rid, None)
            raise BridgeError(f"{method} timed out after {timeout}s")

        if not resp.get("ok"):
            raise BridgeError(f"{method}: {resp.get('error', 'unknown')}")
        return resp.get("data") or {}

    async def call(
        self,
        method: str,
        params: Optional[dict] = None,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        """Chờ JSON-RPC trong worker thread để không chặn event loop."""
        return await asyncio.to_thread(self.call_blocking, method, params, timeout)

    # ------------------------------------------------------------------
    # Watchdog — auto-respawn
    # ------------------------------------------------------------------
    def start_watchdog(
        self, connect_cfg: dict[str, Any] | None = None, enable_e2ee: bool = True
    ) -> threading.Thread:
        """Khởi động watchdog thread giám sát subprocess.

        Khi bridge crash, watchdog sẽ:
        1. Đợi exponential backoff (2s, 4s, 8s, 16s, 32s)
        2. Respawn subprocess
        3. Replay connection state (newClient + connect + connectE2EE)
        4. Emit `bridge_fatal` event nếu vượt quá MAX_RETRIES
        """
        self._connect_cfg = connect_cfg or {}
        self._enable_e2ee = enable_e2ee

        t = threading.Thread(
            target=self._watchdog_loop, daemon=True, name="bridge-watchdog"
        )
        t.start()
        return t

    def _watchdog_loop(self) -> None:
        retries = 0
        while not self._stop_event.is_set():
            # Đợi subprocess thoát
            try:
                self._proc.wait()
            except Exception:
                pass

            if self._stop_event.is_set():
                break

            if retries >= self.MAX_RETRIES:
                print(
                    f"[{datetime.datetime.now()}] Bridge exceeded max retries ({self.MAX_RETRIES}). Giving up."
                )
                self.events.put(
                    {
                        "type": "bridge_fatal",
                        "error": f"max retries exceeded ({self.MAX_RETRIES})",
                        "retries": retries,
                    }
                )
                break

            backoff = self.BASE_BACKOFF ** (retries + 1)
            print(
                f"[{datetime.datetime.now()}] Bridge crashed. "
                f"Respawning in {backoff:.0f}s (attempt {retries + 1}/{self.MAX_RETRIES})"
            )

            # Sleep với check stop mỗi 0.5s để có thể cancel nhanh
            sleep_end = time.monotonic() + backoff
            while time.monotonic() < sleep_end:
                if self._stop_event.is_set():
                    return
                time.sleep(min(0.5, sleep_end - time.monotonic()))

            try:
                self._spawn()
                # Replay connection state
                if self._connect_cfg:
                    self.call_blocking("newClient", self._connect_cfg)
                    self.call_blocking("connect", timeout=120)
                    if self._enable_e2ee:
                        self.call_blocking("connectE2EE", timeout=60)
                print(
                    f"[{datetime.datetime.now()}] Respawn successful (attempt {retries + 1})"
                )
                retries = 0  # Reset sau khi respawn thành công
            except Exception as exc:
                detail = str(exc) if self._log_stderr else type(exc).__name__
                print(f"[{datetime.datetime.now()}] Respawn failed: {detail}")
                retries += 1

    # ------------------------------------------------------------------
    def close(self) -> None:
        self._stop_event.set()
        if self._proc.poll() is None:
            try:
                self.call_blocking("disconnect", timeout=5)
            except BridgeError:
                pass
            try:
                if self._proc.stdin:
                    self._proc.stdin.close()
            except Exception:  # noqa: BLE001
                pass
            try:
                self._proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._proc.kill()
        self._closed = True


# ---------------------------------------------------------------------------
# Cookie helper
# ---------------------------------------------------------------------------

_REQUIRED_COOKIES = ("c_user", "xs", "datr", "fr")

# ---------------------------------------------------------------------------
# Public listener — API tương thích với _listening.py
# ---------------------------------------------------------------------------


class listeningE2EEEvent:
    """Lắng nghe tin nhắn (regular + E2EE).

    Tương thích với `listeningEvent` của _listening.py:
        l = listeningE2EEEvent(dataFB)
        l.connect_mqtt()       # blocking, giữ tên cũ cho tương thích

    Bổ sung:
        @l.on_message
        def handler(evt: dict): ...

        l.send_e2ee_message(chat_jid, "pong",
                            reply_to_id=..., reply_to_sender_jid=...)
    """

    def __init__(
        self,
        dataFB: dict,
        *,
        log_level: str = "none",
        device_path: Optional[str] = None,
        e2ee_memory_only: bool = True,
        enable_e2ee: bool = True,
        binary_path: Optional[str] = None,
        debug_errors: bool = False,
    ) -> None:
        self.dataFB = dataFB
        self.log_level = log_level
        self.device_path = device_path
        self.e2ee_memory_only = e2ee_memory_only
        self.enable_e2ee = enable_e2ee
        self.debug_errors = debug_errors
        self._binary_path_override = binary_path

        self._on_message = None
        self._bridge: Optional[_BridgeProcess] = None
        self._stop = threading.Event()
        self._connected = threading.Event()
        self._e2ee_connected = threading.Event()
        self._startup_error: BaseException | None = None

        self.bodyResults = self._fresh_body()
        self.e2eeBodyResults: dict[str, Any] = {"chatJid": None, "senderJid": None}

        # Compat fields. Do not fetch the full inbox/thread list here: it can
        # block bridge startup for a long time and is not needed by the E2EE RPC listener.
        self.fbt: dict[str, Any] = {}
        self.lastSeqID = None
        self.syncToken = None

    # ------------------------------------------------------------------
    @staticmethod
    def _fresh_body() -> dict[str, Any]:
        return {
            "body": None,
            "timestamp": 0,
            "userID": 0,
            "messageID": None,
            "replyToID": 0,
            "type": None,
            "attachments": {"id": 0, "url": None},
            "mentions": [],
        }

    def on_message(self, fn: Callable[[dict], None]) -> Callable[[dict], None]:
        self._on_message = fn
        return fn

    def get_last_seq_id(self):
        self.lastSeqID = self.fbt.get("last_seq_id")
        print(f"[{datetime.datetime.now()}] last_seq_id: {self.lastSeqID}")
        return self.lastSeqID

    def wait_until_connected(
        self, timeout: float = 60.0, *, require_e2ee: bool = False
    ) -> bool:
        """Đợi listener handshake xong trước khi gửi/đọc event.

        `connect_mqtt_blocking()` thường chạy trong daemon thread. Nếu caller
        gửi message ngay sau `Thread.start()` thì rất dễ đụng race: bridge mới
        spawn nhưng chưa `connect`/`connectE2EE`, poll loop cũng chưa chạy.
        """
        deadline = time.monotonic() + timeout
        if not self._connected.wait(timeout):
            if self._startup_error is not None:
                raise RuntimeError(
                    "E2EE listener failed to start."
                ) from self._startup_error
            return False
        if self._startup_error is not None:
            raise RuntimeError(
                "E2EE listener failed to start."
            ) from self._startup_error
        if not require_e2ee or not self.enable_e2ee:
            return True
        remaining = max(0.0, deadline - time.monotonic())
        if not self._e2ee_connected.wait(remaining):
            if self._startup_error is not None:
                raise RuntimeError(
                    "E2EE listener failed during E2EE handshake."
                ) from self._startup_error
            return False
        return True

    # ------------------------------------------------------------------
    def _build_cookie_dict(self) -> dict[str, str]:
        cks = parse_cookie_string(self.dataFB["cookieFacebook"])
        missing = [c for c in _REQUIRED_COOKIES if c not in cks]
        if missing:
            raise ValueError(
                f"Thiếu cookie bắt buộc cho E2EE bridge: {missing}. "
                f"Cookie hiện có: {list(cks)}"
            )
        keep = {"c_user", "xs", "datr", "fr", "sb", "wd", "presence"}
        return {k: v for k, v in cks.items() if k in keep}

    # ------------------------------------------------------------------
    def connect_mqtt_blocking(self) -> None:
        """Khởi động bridge subprocess + connect Messenger (blocking poll loop).

        Watchdog thread tự động respawn bridge nếu subprocess crash,
        với exponential backoff (2s→32s, tối đa 5 lần).
        Emit `bridge_fatal` event nếu give up.
        """
        binary = (
            Path(self._binary_path_override)
            if self._binary_path_override
            else _resolve_binary()
        )
        self._startup_error = None
        self._connected.clear()
        self._e2ee_connected.clear()
        self._stop.clear()

        try:
            self._bridge = _BridgeProcess(binary, log_stderr=self.debug_errors)

            cfg: dict[str, Any] = {
                "cookies": self._build_cookie_dict(),
                "platform": "facebook",
                "logLevel": self.log_level,
                "e2eeMemoryOnly": self.e2ee_memory_only,
            }
            if self.device_path:
                cfg["devicePath"] = self.device_path

            self._bridge.call_blocking("newClient", cfg)
            info = self._bridge.call_blocking("connect", timeout=120)
            user = info.get("user", {})
            print(
                f"[{datetime.datetime.now()}] Logged in as "
                f"{user.get('name')} ({user.get('id')})"
            )
            self._connected.set()

            if self.enable_e2ee:
                try:
                    self._bridge.call_blocking("connectE2EE", timeout=60)
                    self._e2ee_connected.set()
                    print(f"[{datetime.datetime.now()}] E2EE connected")
                except BridgeError as exc:
                    detail = str(exc) if self.debug_errors else type(exc).__name__
                    print(f"[{datetime.datetime.now()}] E2EE connect failed: {detail}")

            # Khởi động watchdog — auto-respawn khi bridge crash
            self._bridge.start_watchdog(connect_cfg=cfg, enable_e2ee=self.enable_e2ee)

            self._poll_loop()
        except BaseException as exc:
            self._startup_error = exc
            self._connected.set()
            raise

    async def connect_mqtt(self) -> None:
        """Chạy poll loop của bridge ngoài event loop asyncio."""
        await asyncio.to_thread(self.connect_mqtt_blocking)

    def stop(self) -> None:
        self._stop.set()
        self._connected.clear()
        self._e2ee_connected.clear()
        if self._bridge is not None:
            self._bridge.close()
            self._bridge = None

    # ------------------------------------------------------------------
    def _poll_loop(self) -> None:
        """Event dispatch loop — chỉ lắng nghe và dispatch events.

        Watchdog thread xử lý respawn độc lập, poll loop không cần
        quan tâm đến reconnect logic nữa.
        """
        assert self._bridge is not None

        try:
            while not self._stop.is_set():
                try:
                    evt = self._bridge.events.get(timeout=1.0)
                except Empty:
                    continue

                if evt.get("type") == "bridge_fatal":
                    detail = evt.get("error") if self.debug_errors else "details hidden"
                    print(f"[{datetime.datetime.now()}] bridge_fatal: {detail}")
                    break

                self._dispatch(evt)

        finally:
            self.stop()

    # ------------------------------------------------------------------
    def _dispatch(self, evt: dict[str, Any]) -> None:
        etype = evt.get("type")
        data = evt.get("data") or {}

        if etype == "message":
            self._populate_regular(data)
        elif etype == "e2eeMessage":
            self._populate_e2ee(data)
        elif etype == "ready":
            print(
                f"[{datetime.datetime.now()}] ready: "
                f"isNewSession={data.get('isNewSession')}"
            )
        elif etype == "e2eeConnected":
            print(f"[{datetime.datetime.now()}] e2eeConnected")
        elif etype == "disconnected":
            detail = f": {data}" if self.debug_errors else ""
            print(f"[{datetime.datetime.now()}] disconnected{detail}")
        elif etype == "error":
            detail = str(data) if self.debug_errors else "payload hidden"
            print(f"[{datetime.datetime.now()}] bridge error ({detail})")

        if self._on_message:
            try:
                self._on_message(evt)
            except Exception as exc:  # noqa: BLE001
                detail = str(exc) if self.debug_errors else "details hidden"
                print(
                    f"[{datetime.datetime.now()}] handler raised: "
                    f"{type(exc).__name__} ({detail})"
                )

    def _populate_regular(self, msg: dict[str, Any]) -> None:
        body = self._fresh_body()
        body["body"] = msg.get("text")
        body["timestamp"] = msg.get("timestampMs", 0)
        body["userID"] = msg.get("senderId", 0)
        body["messageID"] = msg.get("id")
        body["replyToID"] = msg.get("threadId", 0)
        body["type"] = "thread"
        body["mentions"] = msg.get("mentions", [])

        atts = msg.get("attachments") or []
        if atts:
            first = atts[0]
            body["attachments"]["id"] = (
                first.get("stickerId") or first.get("fileSize") or 0
            )
            body["attachments"]["url"] = first.get("url") or first.get("previewUrl")

        self.bodyResults = body
        self.e2eeBodyResults = {"chatJid": None, "senderJid": None}

    def _populate_e2ee(self, msg: dict[str, Any]) -> None:
        body = self._fresh_body()
        body["body"] = msg.get("text")
        body["timestamp"] = msg.get("timestampMs", 0)
        body["userID"] = msg.get("senderId", 0)
        body["messageID"] = msg.get("id")
        body["replyToID"] = msg.get("threadId", 0)
        body["type"] = "e2ee"
        body["mentions"] = msg.get("mentions", [])

        atts = msg.get("attachments") or []
        if atts:
            first = atts[0]
            body["attachments"]["id"] = first.get("stickerId") or 0
            body["attachments"]["url"] = first.get("url") or first.get("previewUrl")

        self.bodyResults = body
        self.e2eeBodyResults = {
            "chatJid": msg.get("chatJid"),
            "senderJid": msg.get("senderJid"),
        }

    # ------------------------------------------------------------------
    # Helper sender APIs
    def send_message_blocking(
        self, thread_id: int, text: str, reply_to_id: str = ""
    ) -> dict[str, Any]:
        if self._bridge is None:
            raise RuntimeError("Chưa kết nối — gọi connect_mqtt() trước.")
        opts: dict[str, Any] = {"threadId": thread_id, "text": text}
        if reply_to_id:
            opts["replyToId"] = reply_to_id
        return self._bridge.call_blocking("sendMessage", opts)

    async def send_message(
        self, thread_id: int, text: str, reply_to_id: str = ""
    ) -> dict[str, Any]:
        if self._bridge is None:
            raise RuntimeError("Chưa kết nối — gọi connect_mqtt() trước.")
        opts: dict[str, Any] = {"threadId": thread_id, "text": text}
        if reply_to_id:
            opts["replyToId"] = reply_to_id
        return await self._bridge.call("sendMessage", opts)

    def send_e2ee_message_blocking(
        self,
        chat_jid: str,
        text: str,
        reply_to_id: str = "",
        reply_to_sender_jid: str = "",
    ) -> dict[str, Any]:
        if self._bridge is None:
            raise RuntimeError("Chưa kết nối — gọi connect_mqtt() trước.")
        return self._bridge.call_blocking(
            "sendE2EEMessage",
            {
                "chatJid": chat_jid,
                "text": text,
                "replyToId": reply_to_id,
                "replyToSenderJid": reply_to_sender_jid,
            },
        )

    async def send_e2ee_message(
        self,
        chat_jid: str,
        text: str,
        reply_to_id: str = "",
        reply_to_sender_jid: str = "",
    ) -> dict[str, Any]:
        if self._bridge is None:
            raise RuntimeError("Chưa kết nối — gọi connect_mqtt() trước.")
        return await self._bridge.call(
            "sendE2EEMessage",
            {
                "chatJid": chat_jid,
                "text": text,
                "replyToId": reply_to_id,
                "replyToSenderJid": reply_to_sender_jid,
            },
        )
