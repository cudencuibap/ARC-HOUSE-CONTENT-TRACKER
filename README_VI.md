🇻🇳 Tiếng Việt | [🇬🇧 English](README.md)

# 🏛️ Arc House Content Tracker

> Công cụ giúp bạn **tối ưu điểm contribution** trên [community.arc.io](https://community.arc.io):
> tự cào toàn bộ video/bài viết, biết bạn **đã xem cái nào**, và gợi ý **xem gì hôm nay** để ăn đủ điểm.

![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Tool chạy gọn trong **Docker** — bật lên khi cần, xem xong tắt đi, dữ liệu vẫn được giữ lại trên máy bạn. Kết quả xuất ra **file Excel có màu** dễ nhìn.

---

## ✨ Tính năng

- 📥 **Cào toàn bộ content** Arc House (hiện ~**141 items**: video + bài viết) về một file Excel.
- ✅ **Tự đánh dấu đã xem** — đọc lịch sử contribution thật của bạn qua GraphQL, không cần tick tay.
- 📊 **Dashboard** hiển thị **lifetime points**, tiến trình đã xem/đã đọc, và quota hôm nay.
- 🎯 **Đề xuất tối ưu theo quota ngày** (4 video × 4đ + 5 bài × 2đ = **27đ/ngày**) — in sẵn link để copy mở browser.
- 🚫 **Report link die → blacklist**: gặp link hỏng thì báo một lần, tool **không bao giờ gợi ý lại**.
- 🎨 **Excel có màu**: dòng **🟩 xanh** = đã xem, dòng **⬜ xám** = đã blacklist → nhìn phát biết ngay.

---

## 📋 Yêu cầu

| Cần gì | Ghi chú |
|--------|---------|
| 🐳 **Docker Desktop** | Tải miễn phí tại <https://www.docker.com/products/docker-desktop/> |
| 👤 **Tài khoản community.arc.io** | Bạn phải đã đăng nhập được trên trình duyệt (thường login bằng Gmail) |

> Không cần cài Python, không cần cài thư viện gì cả — Docker lo hết.

---

## 🚀 Cài đặt — hướng dẫn từng bước cho người mới

### Bước 1 — Cài Docker Desktop

1. Vào <https://www.docker.com/products/docker-desktop/> → tải bản cho **Windows**.
2. Chạy file cài đặt, bấm Next đến hết, khởi động lại máy nếu nó yêu cầu.
3. Mở **Docker Desktop** lên (tìm trong Start Menu). Lần đầu sẽ mất ~1 phút.
4. Đợi đến khi **biểu tượng con cá voi 🐳 ở góc dưới phải màn hình chuyển sang màu xanh** (báo "Docker Desktop is running"). Xong là sẵn sàng.

> ⚠️ Mỗi lần dùng tool, Docker Desktop **phải đang chạy** (icon xanh). Tắt Docker thì tool không chạy được.

### Bước 2 — Tải code về máy

Chọn **một trong hai cách**:

**Cách A — Tải ZIP (dễ nhất, không cần biết Git):**
1. Vào trang GitHub của project → bấm nút xanh **`< > Code`** → **Download ZIP**.
2. Giải nén ra. Đổi tên / di chuyển thư mục về đúng đường dẫn: **`C:\arc-house-community-tool`**

**Cách B — Dùng Git (nếu đã cài Git):**
```powershell
git clone https://github.com/cudencuibap/ARC-HOUSE-CONTENT-TRACKER.git C:\arc-house-community-tool
```

### Bước 3 — Lấy cookie đăng nhập

👉 Đây là bước quan trọng nhất, đọc kỹ **[section ⭐ Lấy cookie](#-lấy-cookie-quan-trọng-nhất)** bên dưới.

### Bước 4 — Chạy tool

- **Cách dễ nhất:** mở thư mục `C:\arc-house-community-tool`, **double-click `run.bat`**.
  - Lần đầu sẽ tự build (1–2 phút). Các lần sau vào thẳng menu.
- **Hoặc** chạy bằng lệnh trong PowerShell:
  ```powershell
  cd C:\arc-house-community-tool
  docker compose run --rm arc-tracker
  ```

---

## ⭐ Lấy cookie (QUAN TRỌNG NHẤT)

### 🤔 Vì sao phải lấy cookie?

- Tool cần biết **bạn đã xem content nào rồi** để khỏi gợi ý lại.
- Thông tin đó nằm trong trang **"My Contributions"** — trang **cá nhân** của bạn.
- Trang cá nhân chỉ mở được **khi đã đăng nhập**.
- **Cookie** giống như "tem dán" trên trình duyệt nói với Arc House rằng *"tôi chính là người vừa đăng nhập"*. Đưa cookie đó cho tool → tool đọc được trang cá nhân giùm bạn.

> Nếu **không** đặt cookie, tool vẫn chạy nhưng chỉ cào content public, **không tự đánh dấu đã xem** được.

### ⚠️ Cookie này có an toàn không? (đọc kỹ)

- ✅ Cookie **CHỈ** nằm trong file `config/cookie.txt` **trên máy bạn**. Không gửi lên server nào của tool, **không gửi cho tác giả**, không gửi cho Claude/AI nào.
- ✅ Tool **open-source** — ai cũng đọc được file `arc_tracker.py` để tự kiểm chứng: cookie chỉ dùng để gọi API của **chính Arc House**, không gửi đi đâu khác.
- ✅ Cookie **KHÁC** mật khẩu Gmail/Google. Lấy cookie **không làm lộ mật khẩu** của bạn.
- ✅ File `config/cookie.txt` đã được `.gitignore` loại trừ → khi bạn push code lên GitHub của mình, **cookie KHÔNG bị đẩy lên theo**.
- ✅ Cookie **tự hết hạn** sau vài ngày/tuần. Hết hạn thì chỉ cần copy lại cái mới.
- ✅ Bạn **thu hồi được bất cứ lúc nào**: chỉ cần **logout** khỏi community.arc.io trên trình duyệt là cookie cũ vô hiệu.
- ❌ **KHÔNG** share cookie cho người khác hoặc paste lên forum/group public. Ai có cookie có thể đăng nhập **tài khoản Arc** của bạn (nhưng **không** vào được Gmail của bạn).
- ❌ **KHÔNG** commit file `config/cookie.txt` lên GitHub public (đã có `.gitignore` bảo vệ sẵn — đừng tự ý xoá dòng đó).

### 🍪 Cách lấy cookie — từng bước

1. Mở **Chrome** (hoặc Edge), vào <https://community.arc.io> và **đăng nhập** bằng Gmail như bình thường.
2. Vào trang lịch sử cá nhân: <https://community.arc.io/home/contributors/my-contributions>
3. Nhấn phím **`F12`** để mở **DevTools**, chọn tab **`Network`** (Mạng).
4. Trên thanh filter của tab Network, bấm nút lọc **`Doc`** (loại document — đừng chọn Media/JS/CSS).
5. Nhấn **`F5`** để tải lại trang. Trong danh sách request hiện ra, **click vào request đầu tiên** (thường trùng tên trang).
6. Panel bên phải mở ra → tab **`Headers`** → cuộn xuống mục **`Request Headers`** → tìm dòng bắt đầu bằng **`cookie:`**
7. **Bôi đen toàn bộ** giá trị dài phía sau chữ `cookie:` → chuột phải **Copy value** (hoặc `Ctrl+C`).
8. Mở **Notepad**, **dán** vào (đúng **1 dòng duy nhất**, không xuống dòng), rồi **Lưu** thành file:
   ```
   C:\arc-house-community-tool\config\cookie.txt
   ```
   > Mẹo: trong thư mục `config` đã có sẵn file mẫu `cookie.txt.example` hướng dẫn lại các bước này.

🔧 **Về User-Agent:** tool tự dùng đúng User-Agent để khớp với cookie của bạn — **bạn không cần làm gì thêm**.

---

## 🕹️ Cách dùng

Khi chạy, tool tự refresh + đồng bộ + hiện dashboard + đề xuất, rồi vào **menu 3 mục**:

| Phím | Chức năng | Khi nào dùng |
|------|-----------|--------------|
| **1** | 🎯 **Đề xuất hôm nay** | Bấm để tool cào lại content, đồng bộ lịch sử đã xem, rồi in link nên xem hôm nay (video trước vì 4đ > 2đ). Xem xong bấm lại `1` để cập nhật. |
| **2** | 🚫 **Report link die** | Khi gặp link hỏng/không xem được — bấm để hiện danh sách đang đề xuất, nhập số (vd `1,3,5`) → tool **blacklist**, không gợi ý lại nữa. |
| **3** | 📊 **Dashboard** | Xem nhanh lifetime points, đã xem/đọc bao nhiêu, và hôm nay còn mấy slot. |
| **0** | 🚪 **Thoát** | Đóng tool. Dữ liệu vẫn được giữ trên máy. |

**Quy trình hằng ngày gợi ý:**
1. Chạy `run.bat` → đọc phần **Đề xuất**.
2. Copy link → mở Chrome → xem/đọc cho đủ.
3. Quay lại bấm `1` để đồng bộ (bài vừa xem tự đánh dấu từ lịch sử thật).
4. Link nào hỏng → bấm `2` để report.
5. Hết quota → bấm `0` thoát.

> 🚫 **Bỏ blacklist:** mở `data/arc-content.xlsx`, xoá chữ `Yes` ở cột **Blacklist** của dòng đó, lưu lại → lần chạy sau item được đề xuất lại bình thường.

### 🌐 Đổi ngôn ngữ (Anh / Việt)

Lần chạy **đầu tiên** tool sẽ hỏi bạn chọn **English / Tiếng Việt**, rồi lưu vào `config/language.txt` và **không hỏi lại** những lần sau. Muốn đổi ngôn ngữ: **xoá file `config/language.txt`** → lần chạy kế tiếp tool sẽ hỏi lại.

---

## 🛟 Troubleshooting (sự cố thường gặp)

| Triệu chứng | Cách xử lý |
|-------------|-----------|
| **"Docker chưa chạy" / lệnh báo lỗi không kết nối Docker** | Mở **Docker Desktop**, đợi icon 🐳 chuyển xanh rồi chạy lại. |
| **Không tự đồng bộ được lịch sử "đã xem"** | Cookie đã **hết hạn** → làm lại [section Lấy cookie](#-lấy-cookie-quan-trọng-nhất), copy cookie mới. |
| **"Loi cao content" / báo lỗi mạng** | Kiểm tra **internet**, thử lại sau vài giây. |
| **Tool báo lỗi 403 / Forbidden** | Cookie **không khớp User-Agent** hoặc đã bị thu hồi → lấy lại cookie mới từ DevTools (theo đúng các bước trên). |

---

## 🗂️ Cấu trúc project

```
arc-house-community-tool/
├── run.bat                   <- double-click để chạy (Windows)
├── arc_tracker.py            <- toàn bộ logic (cào, parse, Excel, menu)
├── nonce_gen.js              <- sinh header chống bot (chạy bằng Node trong Docker)
├── nonce_chunk.js            <- JS của site dùng cho nonce
├── Dockerfile                <- công thức build image
├── docker-compose.yml        <- cấu hình chạy container
├── requirements.txt          <- thư viện Python
├── README.md                 <- file bạn đang đọc
├── CLAUDE.md                 <- ghi chú kỹ thuật cho Claude Code
├── LICENSE                   <- giấy phép MIT
├── config/
│   ├── cookie.txt.example    <- hướng dẫn lấy cookie
│   └── cookie.txt            <- (bạn tự tạo) cookie đăng nhập — KHÔNG push GitHub
└── data/
    ├── arc-content.xlsx      <- file Excel kết quả (sinh ra khi chạy)
    └── debug/                <- log JSON khi cần debug
```

> 📦 Dữ liệu nằm trong `data/` **trên máy bạn** → tắt container không mất. Có thể bỏ folder này vào OneDrive để đồng bộ giữa nhiều máy.

---

## 🤝 Đóng góp (Contributing)

Rất hoan nghênh! Nếu bạn muốn cải thiện tool: fork repo, tạo branch mới, commit thay đổi, rồi mở **Pull Request** mô tả rõ bạn sửa gì và vì sao. Báo lỗi/ý tưởng thì mở **Issue**. Vui lòng **đừng** đính kèm cookie hay dữ liệu cá nhân trong issue/PR.

---

## 📄 License

Phát hành theo giấy phép **MIT** — xem file [LICENSE](LICENSE). Tự do dùng, sửa, chia sẻ.

---

> ℹ️ Phần đọc lịch sử cá nhân được xây theo API GraphQL thật của Arc House. Site có thể đổi cấu trúc/deploy lại → đôi khi cần tinh chỉnh nhẹ. Xem `CLAUDE.md` nếu bạn muốn dùng **Claude Code** để bảo trì nhanh.
