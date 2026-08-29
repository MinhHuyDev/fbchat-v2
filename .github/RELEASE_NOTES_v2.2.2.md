# 🚀 Release Notes - V2.2.2

Bản cập nhật V2.2.2 tập trung gia cố E2EE, quyền riêng tư, packaging và quy trình
release, đồng thời bổ sung các tính năng quản lý bài viết trên Timeline Facebook
qua GraphQL API nội bộ.

## ✨ Tính năng mới (New Features)

### 1. Xoá bài viết vào thùng rác (`_deletePost.py`)
- Hỗ trợ di chuyển các bài viết trên dòng thời gian (Timeline) vào thùng rác an toàn thông qua GraphQL mutation `useCometTrashPostMutation`.
- Tránh việc xoá vĩnh viễn ngay lập tức (dễ khôi phục nếu lỡ tay).
- **Hỗ trợ phân loại:**
  - `typePost="my_post"`: Dành cho bài viết chính chủ (bạn tự viết).
  - `typePost="others"`: Dành cho bài viết share hoặc của người khác đăng lên tường.

### 2. Lưu trữ bài viết (`_archivePost.py`)
- Hỗ trợ ẩn bài viết khỏi Timeline và chuyển vào Kho lưu trữ (Archive) sử dụng `useCometArchivePostMutation`.
- Phù hợp với nhu cầu dọn dẹp profile nhưng không muốn xoá đi kỷ niệm.
- Hỗ trợ tham số `typePost` tương tự như tính năng xoá bài viết.

---

## 🛠 Fixes & Chores
- Cập nhật chuẩn hoá tài liệu API (`DOCS.md`, `README.md`, `README_EN.md`) cho hai module mới.
- Khắc phục lỗi copy-paste nhầm key parse payload trong `_deletePost.py` từ các bản nháp trước.
- Loại bỏ các comment/docstring không đạt chuẩn để tối ưu clean code.

## 🔒 Bảo mật và độ tin cậy

- Bridge E2EE dùng `crypto/rand` cho `AdvSecretKey`; lifecycle identity, session
  và prekey được lưu đúng thay vì trả thành công giả.
- Device state được serialize và ghi bằng temp file + `fsync` + atomic rename để
  tránh truncate, race và rollback sau crash.
- Mutation persistence thất bại sẽ rollback state trong RAM; LID/account/device
  metadata được giữ qua restart, còn callback snapshot không chặn Signal ratchet.
- Auto-download bridge pin đúng tag `v2.2.2`, bắt buộc SHA-256 đóng kèm wheel,
  kiểm tra mọi redirect và fail closed khi artifact không khớp.
- File config cookie có quyền riêng tư; log nội dung chat và traceback bị che
  mặc định.
- Sửa shutdown listener async, parser mutation báo thành công giả và 7 lỗi
  compile do vị trí `from __future__`.
- Đồng bộ connect/disconnect để không hồi sinh socket sau shutdown; yêu cầu gửi
  E2EE giờ fail closed thay vì âm thầm rơi xuống transport thường.

## 📦 Packaging và CI

- Wheel export trực tiếp `_core`, `_features`, `_messaging`; smoke test chạy trên
  cả wheel và editable install trong virtual environment sạch.
- CI chạy pytest trên Python 3.10-3.13, Ruff, Black, mypy, compileall, Go
  test/vet và JavaScript syntax.
- Release phát hành `SHA256SUMS`, provenance attestation và wheel chứa checksum
  của đúng năm bridge binary.
