# 🚀 fbchat-v2 v2.3.1 — Bổ sung tương tác cảm xúc bài viết và tối ưu hóa chất lượng

> **Trạng thái:** Đã phát hành chính thức trên PyPI (`fbchat-v2==2.3.1`) và đồng bộ trên nhánh `main` cùng nhánh `pypi`.

`v2.3.1` là bản cập nhật tính năng (feature release) và hoàn thiện chất lượng code sau đợt đại tu `v2.3.0`. Bản phát hành này bổ sung tính năng tương tác cảm xúc (Reaction) trực tiếp trên dòng thời gian cá nhân của bạn bè, đồng bộ lại toàn bộ public exports của `_features._facebook`, chuẩn hóa telemetry chống checkpoint bot và siết chặt quality gate CI.

## ✨ Điểm nổi bật

### 1. Tính năng mới: Tương tác cảm xúc bài viết (`_reactionPost`)
- Thêm module `_features._facebook._reactionPost.func(dataFB, postID, typeReactions="LIKE", *, client=None)`:
  - Cho phép thả đầy đủ 7 loại cảm xúc: `LIKE`, `LOVE`, `CARE` (hoặc `SUPPORT`), `HAHA`, `WOW`, `SAD` (hoặc `SORRY`), `ANGRY` (hoặc `ANGER`).
  - Hỗ trợ gỡ cảm xúc linh hoạt thông qua các alias: `UNDO`, `UNREACT`, `NONE`.
  - Hỗ trợ định dạng chuỗi không phân biệt hoa thường (`case-insensitive`) như `"like"`, `"Love"`, `"care"`.
  - Tự động chuẩn hóa `feedback_id`: Tự động encode base64 định dạng `feedback:<postID>` nếu truyền ID bài viết thô, hoặc giữ nguyên nếu đã là token Base64 feedback hợp lệ, chống hoàn toàn lỗi double-encoding.
  - Sử dụng GraphQL mutation `CometUFIFeedbackReactMutation` (doc_id `27646120298312844`) tương thích với giao diện Comet hiện đại của Facebook.

### 2. Tối ưu Telemetry và bảo mật tài khoản
- Khắc phục referrer bất thường: Thay thế referrer tĩnh trỏ về trang xác thực 2 bước (`/two_step_verification/two_factor/`) bằng profile path hợp lệ `/{actor_id}`, loại bỏ hoàn toàn nguy cơ bị hệ thống phát hiện hành vi bất thường của Meta gắn cờ bot hoặc checkpoint tài khoản.
- Khắc phục hardcode attribution: Chuyển `attribution_id_v2` sang f-string chuẩn ở value với epoch milliseconds, `jazoest` và `actor_id` động của phiên đăng nhập thay cho UID tĩnh ma.
- Dọn dẹp sạch sẽ các payload comment tracking rác bị bỏ quên trong mã nguồn.

### 3. Đồng bộ Public Exports (`_features._facebook.__all__`)
- Bổ sung `_reactionPost`, `_archivePost`, `_deletePost` vào danh sách export chính thức `__all__` của `_features._facebook.__init__.py`, khôi phục các tính năng bị bỏ quên trước đây.

### 4. Gia cố CI / Quality Gate
- Dọn dẹp dead import: Gỡ bỏ import `random` không sử dụng trong `_reactionPost.py`, khắc phục lỗi `F401` giúp quality gate của GitHub Actions (`ruff check src tests scripts`) đạt 100% pass.
- Đảm bảo 149/149 test suite pytest vượt qua trên Python 3.10–3.14.

## 📖 Hướng dẫn sử dụng tính năng mới

```python
import asyncio
from _core._session import dataGetHome
from _features._facebook import _reactionPost

async def main():
    cookies = "PASTE_YOUR_COOKIES_HERE"
    dataFB = dataGetHome(cookies)

    # 1. Thả tim vào bài viết
    result_love = await _reactionPost.func(dataFB, postID="123456789012345", typeReactions="LOVE")
    print(result_love)
    # Output: {'success': 1, 'messages': 'Thả reaction thành công!'}

    # 2. Thả Haha (chấp nhận chữ thường)
    result_haha = await _reactionPost.func(dataFB, postID="123456789012345", typeReactions="haha")
    print(result_haha)

    # 3. Gỡ cảm xúc đã thả
    result_undo = await _reactionPost.func(dataFB, postID="123456789012345", typeReactions="UNREACT")
    print(result_undo)
    # Output: {'success': 1, 'messages': 'Gỡ reaction thành công!'}

asyncio.run(main())
```

## 📦 Cài đặt và Nâng cấp

Bản phát hành `v2.3.1` đã sẵn sàng trên PyPI:

```bash
python -m pip install --upgrade "fbchat-v2==2.3.1"
```

Đối với git repository checkout:

```bash
git checkout main
git pull origin main
```
