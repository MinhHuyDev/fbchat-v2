"""Verify the wheel layout and the documented top-level import contract."""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
import zipfile
from email.parser import Parser
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DISTIBUTION_NAME = "fbchat-v2"
EXPECTED_VERSION = "2.2.2"
PACKAGE_NAMES = ("_core", "_features", "_messaging")
REQUIRED_WHEEL_MEMBERS = {
    "_core/__init__.py",
    "_core/_permissions.py",
    "_features/_facebook/__init__.py",
    "_features/_facebook/_unFriend.py",
    "_features/_thread/__init__.py",
    "_messaging/__init__.py",
}


def verify_wheel(wheel_path: Path) -> None:
    """Ensure the wheel exposes packages at top level instead of under ``src``."""
    if not wheel_path.is_file():
        raise FileNotFoundError(f"Không tìm thấy wheel: {wheel_path}")

    with zipfile.ZipFile(wheel_path) as archive:
        members = set(archive.namelist())
        metadata_files = sorted(
            member for member in members if member.endswith(".dist-info/METADATA")
        )
        if len(metadata_files) != 1:
            raise RuntimeError(
                "Wheel phải chứa đúng một file metadata, "
                f"nhưng tìm thấy {len(metadata_files)}"
            )
        metadata = Parser().parsestr(
            archive.read(metadata_files[0]).decode("utf-8", errors="strict")
        )

    missing = sorted(REQUIRED_WHEEL_MEMBERS - members)
    if missing:
        raise RuntimeError(f"Wheel thiếu file bắt buộc: {', '.join(missing)}")
    if any(member == "src" or member.startswith("src/") for member in members):
        raise RuntimeError("Wheel vẫn đóng gói namespace sai dưới thư mục src/")
    if metadata.get("Name") != DISTIBUTION_NAME:
        raise RuntimeError(f"Tên distribution không đúng: {metadata.get('Name')!r}")
    if metadata.get("Version") != EXPECTED_VERSION:
        raise RuntimeError(
            "Version trong wheel không đúng: "
            f"{metadata.get('Version')!r} != {EXPECTED_VERSION!r}"
        )


def verify_imports() -> None:
    """Import the public package roots and the exported unfriend feature."""
    imported = [importlib.import_module(package) for package in PACKAGE_NAMES]
    if any(module is None for module in imported):  # pragma: no cover - defensive
        raise RuntimeError("Không import được đầy đủ package công khai")

    try:
        installed_version = version(DISTIBUTION_NAME)
    except PackageNotFoundError as exc:
        raise RuntimeError(f"Chưa cài distribution {DISTIBUTION_NAME}") from exc
    if installed_version != EXPECTED_VERSION:
        raise RuntimeError(
            f"Version đã cài không đúng: {installed_version!r} != {EXPECTED_VERSION!r}"
        )

    facebook = importlib.import_module("_features._facebook")
    exported = getattr(facebook, "__all__", ())
    if "_unFriend" not in exported:
        raise RuntimeError("_features._facebook.__all__ chưa export _unFriend")
    if importlib.util.find_spec("_features._facebook._unFriend") is None:
        raise RuntimeError("Không tìm thấy module _features._facebook._unFriend")
    importlib.import_module("_features._facebook._unFriend")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "wheel",
        nargs="?",
        type=Path,
        help="Wheel cần kiểm tra nội dung; bỏ trống khi smoke-test editable install.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.wheel is not None:
        verify_wheel(args.wheel)
    verify_imports()
    print("Distribution smoke test: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
