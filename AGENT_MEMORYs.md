# Agent Memories

## 2026-08-29 — Đồng bộ refactor v2.3.0 và phát hành PyPI

### Mục tiêu
- Đồng bộ runtime refactor từ `fbchat-v2/main` sang checkout đóng gói `fbchat-v2-pypi`, push nhánh `pypi` và phát hành distribution `fbchat-v2==2.3.0`.

### Đã thực hiện
- Port 47 file tracked từ source commit `5f36a2c4f39e23c9bac6bbee9587bd225e7d17d5` vào `src/fbchat_v2`, gồm 42 file cập nhật và 5 module mới.
- Giữ public namespace `fbchat_v2.*` của các bản PyPI trước; cập nhật metadata, README VI/EN, CHANGELOG, hướng dẫn packaging và license classifier sang Apache-2.0.
- Sửa blocking listener gọi nhầm coroutine bằng `func_blocking()` dùng HTTP client sync; thêm regression test.
- Anchor allowlist sdist để không kéo README/LICENSE từ `.venv*`, cache, test hoặc artifact cũ vào package.
- Commit release `d0ec36ad9e3e9589e46e9e6c42caa6840e1f1a23` (`feat(pypi): publish refactored v2.3.0 package`) đã push fast-forward lên `origin/pypi`.

### Quyết định kỹ thuật
- Không merge hai branch vì `pypi` và `main` không có common ancestor; dùng corrective snapshot commit trên lịch sử riêng của `pypi`.
- Không copy `src/config.json`, `.venv*`, `dist/`, cache, source test script hoặc Go submodule.
- Không tạo tag/GitHub Release ngoài phạm vi. Vì chưa có asset/checksum bridge `v2.3.0`, auto-download E2EE cố ý fail-closed; bridge tự build cùng version qua `FBCHAT_E2EE_BIN` vẫn được hỗ trợ.

### Kiểm tra
- Fresh CPython 3.11: compileall, Ruff, Black và mypy 43 source file đều đạt.
- 144/144 runtime test source đã namespace-hoá và 2/2 regression test package đều đạt.
- Wheel/sdist build sạch, Twine strict, member/metadata audit, namespace smoke, `pip check` và fresh-install riêng từng artifact đều đạt.
- Wheel build trực tiếp và wheel dựng lại từ sdist có cùng SHA-256 `48eed1f81b74300ab0afa48f68bb9d450b0ab6b37a4bacfae9d8fe4f99eb9fff`.

### Việc còn lại
- Upload PyPI đang chờ credential: Twine chạy non-interactive với username `__token__` đã dừng trước upload bằng lỗi `Credential not found for API token`; máy không có `.pypirc`, biến môi trường token hoặc GitHub CLI để dùng secret.
- PyPI `2.3.0` vẫn chưa tồn tại sau lần thử an toàn. Khi credential được nạp, upload đúng hai artifact trong temp validation, rồi xác minh PyPI JSON và clean-install trực tiếp từ PyPI.
