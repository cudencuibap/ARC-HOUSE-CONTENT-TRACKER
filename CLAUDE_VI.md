🇻🇳 Tiếng Việt | [🇬🇧 English](CLAUDE.md)

# CLAUDE.md — Agent guide (Arc House Content Tracker)

> Tài liệu cho **AI agent** (Claude Code, Cursor, …) khi user clone repo về và nhờ
> setup / sử dụng / maintain tool. Agent đọc file này để nắm kiến trúc và các tác vụ
> thường gặp. Viết tiếng Việt, giữ technical terms bằng tiếng Anh.

---

## 1. Project overview

Tool theo dõi content trên **community.arc.io** để tối ưu điểm contribution: cào toàn bộ
video/article public, đọc lịch sử "đã xem" của user qua GraphQL, tự đánh dấu, rồi đề xuất
nên xem gì hôm nay theo quota (4 video + 5 article = 27đ/ngày). Output ra Excel có màu.
User là người Việt, dùng trên Windows, chạy qua Docker.

**Tech stack:** Python 3.12 · Docker / docker-compose · `requests` (HTTP) · `openpyxl`
(Excel) · GraphQL (API của Arc) · Node.js (chỉ để sinh `x-nonce`).

---

## 2. Kiến trúc files

| File | Vai trò |
|------|---------|
| `arc_tracker.py` | **Toàn bộ logic**: scrape GraphQL, parse, merge, Excel I/O, menu CLI. Entrypoint. |
| `Dockerfile` | Image `python:3.12-slim` + cài Node.js (cho nonce). Chỉ COPY `arc_tracker.py`, `nonce_gen.js`, `nonce_chunk.js`. |
| `docker-compose.yml` | Service `arc-tracker`; mount `./data` → `/data`, `./config` → `/config`; `stdin_open`+`tty` để menu chạy. |
| `requirements.txt` | `requests`, `openpyxl`, `beautifulsoup4`. |
| `run.bat` | Windows launcher — double-click để `docker compose run`. |
| `nonce_gen.js` | Script Node nhận `x-client`, gọi hàm trong `nonce_chunk.js` → in `x-nonce` ra stdout. |
| `nonce_chunk.js` | JS bundle bóc từ site, chứa `generateNonce`. Đi kèm image; bản refresh ghi vào `/data/nonce_chunk.js`. |
| `config/cookie.txt` | **User tự tạo**, cookie đăng nhập. **gitignored** — không bao giờ commit. |
| `config/cookie.txt.example` | Template hướng dẫn lấy cookie (an toàn để commit). |
| `data/arc-content.xlsx` | Output Excel. **gitignored** (chỉ giữ `data/.gitkeep`). |
| `data/debug/*` | Dump JSON khi debug (vd `contribution_logs.json`). **gitignored.** |

---

## 3. Kiến thức kỹ thuật quan trọng

- **Nền tảng:** community.arc.io chạy trên **Gradual/Circle** — Next.js SPA, data lấy qua **GraphQL**.
- **Endpoint:** `POST https://community.arc.io/api/graphql`. Tenant "Arc House" id nằm trong `TENANT_ID`.
- **Auth (đọc trong `make_session()` + `gql()`):**
  - `Cookie` — từ `config/cookie.txt` (chứa session + `cf_clearance` của Cloudflare). Session token nằm trong cookie, **không** truyền Bearer riêng.
  - `x-client` — chuỗi version build của site (`X_CLIENT`); server check HMAC theo giá trị này, phải **khớp** với chuỗi dùng để sinh nonce.
  - `x-nonce` — anti-bot token, **sinh tươi mỗi request** bằng Node: `gen_nonce()` → chạy `nonce_gen.js` với `nonce_chunk.js`.
- **Cloudflare:** `cf_clearance` trong cookie **gắn với User-Agent**. `USER_AGENT` trong code **phải khớp** UA của browser lúc lấy cookie, nếu không → **403**.
- **Lịch sử "đã xem":** query `MyContributionLogs` (xem `Q_LOGS`) → lọc `contributionRole.name` ∈ {`Watch a Video`, `Read Content`} → lấy `group.title` + `occurredAt`. Trang chứa data: `/home/contributors/my-contributions`.
- **Lifetime points:** query `myTenantUser.totalContributionPoints` (`Q_POINTS`).
- **Content public:** `getContentPageContents` (trang chính, có pagination) + `getPaginatedCollectionPageContents` cho từng slug trong `COLLECTION_SLUGS`.
- Tất cả secret/UA/x-client đều đọc được override qua **env** (`ARC_COOKIE`, `ARC_USER_AGENT`, `ARC_X_CLIENT`).

---

## 4. Các tác vụ thường gặp (template cho agent)

### 4.1. "Giúp tôi setup tool lần đầu"
1. Verify Docker Desktop đang chạy: `docker info` (lỗi → bảo user mở Docker Desktop, đợi icon 🐳 xanh).
2. Check cookie: `Test-Path config/cookie.txt`. Chưa có → hướng dẫn 4.2 (vẫn chạy được nhưng không sync lịch sử).
3. `docker compose build`
4. `docker compose run --rm arc-tracker`

### 4.2. "Cookie hết hạn, giúp tôi lấy lại"
Hướng dẫn user (agent **không** tự làm được vì cần browser của user):
DevTools (`F12`) → tab **Network** → filter **Doc** → `F5` → click request đầu tiên →
**Request Headers** → copy toàn bộ giá trị sau `cookie:` → ghi đè `config/cookie.txt` (1 dòng).
**KHÔNG** echo/print nội dung cookie ra terminal; **KHÔNG** commit file.

### 4.3. "Tool báo 403/401 dù cookie mới"
Nguyên nhân hay gặp: `USER_AGENT` trong `arc_tracker.py` **không khớp** UA của browser lúc user lấy cookie (`cf_clearance` gắn với UA). Xin user UA thật (DevTools → request header `user-agent`) rồi sửa hằng `USER_AGENT` (hoặc set env `ARC_USER_AGENT`). Phụ: cookie thiếu `cf_clearance` → bảo user lấy lại từ chính tab đã qua Cloudflare.

### 4.4. "Tool báo lỗi GraphQL nonce"
`nonce_chunk.js` là JS bóc từ site, chứa `generateNonce`. Site deploy lại → hàm/`x-client` đổi.
Code đã có `refresh_nonce_chunk()` tự tải bundle mới khi `gen_nonce()` fail. Nếu vẫn lỗi: dump JS
bundle mới từ DevTools → Network (file `.js` chứa `generateNonce` + `36035:function`), extract lại,
ghi đè `nonce_chunk.js`, và cập nhật `X_CLIENT` cho khớp build mới.

### 4.5. "Thêm collection URL mới để cào"
Trong `arc_tracker.py`, thêm slug vào list **`COLLECTION_SLUGS`**. `fetch_public_content()` tự
duyệt từng slug qua `getPaginatedCollectionPageContents`. Slug lấy từ URL collection trên site.

### 4.6. "Sửa code xong, build lại"
```powershell
docker compose build
docker compose run --rm arc-tracker
```

### 4.7. "Push update lên GitHub"
```powershell
git status                      # verify cookie/data KHONG xuat hien
git ls-files | Select-String cookie   # chi duoc thay cookie.txt.example
git add .
git commit -m "..."
git push
```

---

## 5. Nguyên tắc agent PHẢI tuân thủ

- ⚠️ **TUYỆT ĐỐI không commit/push** `config/cookie.txt`, `data/arc-content.xlsx`, `data/debug/*`.
  **Verify `git ls-files` trước mỗi commit** (chỉ được phép thấy `cookie.txt.example`).
- **Không hard-code** cookie/token vào code — luôn đọc từ `config/cookie.txt` hoặc env.
- **Không phá logic giữ trạng thái:** khi refresh, item đã `"Da xem"` không bị reset; cột `Blacklist`
  do user sửa tay (xóa `"Yes"`) phải được tôn trọng — `sync()` chỉ update Title/URL, không đụng Status/Blacklist.
- Khi user paste cookie hoặc cURL có cookie: xử lý **ngay trong local code**, **KHÔNG** echo/log/print cookie ra terminal.
- Site Arc có thể đổi API/Cloudflare policy bất kỳ lúc nào → khi vỡ, agent dò lại từ **DevTools dump của user** (không đoán mò).

---

## 6. Cấu trúc data Excel

10 cột: `ID, Type, Title, URL, Points, Status, DateAdded, DateViewed, Note, Blacklist`.

- `Type`: `Video` | `Article`. `Points`: 4 (video) | 2 (article).
- `Status`: `"Chua xem"` | `"Da xem"`.
- `Blacklist`: `"Yes"` | rỗng (item blacklist không bao giờ xuất hiện trong đề xuất).
- **Tô màu (trong `save_excel()`):** `Da xem` → fill **C6EFCE** (xanh) toàn dòng; `Blacklist=Yes` → fill **D9D9D9** (xám). **Ưu tiên xanh** nếu một dòng vừa `Da xem` vừa `Blacklist`.

---

## 7. Menu tool (3 mục)

| Phím | Chức năng |
|------|-----------|
| 1 | **Đề xuất hôm nay** — `sync()` (cào + đồng bộ lịch sử + points) rồi in link tối ưu. |
| 2 | **Report link die** — hiện item đang đề xuất, nhập số (vd `1,3,5`) → set `Blacklist=Yes`. |
| 3 | **Dashboard** — lifetime points + tiến trình + quota hôm nay (đọc từ contribution log thật). |
| 0 | Thoát. |

> Lưu ý: menu chỉ chạy khi có TTY (`sys.stdin.isatty()`); chạy non-TTY (CI/pipe) tool chỉ in dashboard+đề xuất 1 lần rồi thoát.

---

## 8. i18n (EN/VI) — QUAN TRỌNG khi sửa text

- **Mọi string UI** nằm trong dict `TRANSLATIONS = {"en": {...}, "vi": {...}}`. Lấy qua `t(key, **kwargs)` (fallback `en` nếu thiếu key). **Không hard-code** string hiển thị mới — thêm key vào **cả 2** ngôn ngữ.
- Biến global `LANG` set bởi `select_language()` lúc khởi động: đọc `config/language.txt` (`en`/`vi`); chưa có + có TTY → hỏi user rồi lưu; non-TTY → mặc định `en`. User đổi ngôn ngữ bằng cách xoá `config/language.txt`.
- ⚠️ **INTERNAL vs DISPLAY (đừng phá):** giá trị lưu trong Excel luôn là **internal, tiếng Việt cố định** — `Status` = `"Chua xem"`/`"Da xem"`, `Blacklist` = `"Yes"`, `Type` = `"Video"`/`"Article"`. **Tuyệt đối không** dịch các giá trị này khi load/save → data cũ tương thích 100%. Chỉ khi **hiển thị ra terminal** mới dịch (vd helper `status_display()` map sang `t("status_viewed")`).
- `config/language.txt`: chỉ là cấu hình UI cá nhân (không bí mật). Không cần commit; mỗi máy tự sinh khi chạy lần đầu.
