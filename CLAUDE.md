# CLAUDE.md — Huong dan cho Claude Code

Day la project **Arc House Content Tracker**: tool theo doi content tren community.arc.io
de toi uu diem contribution. Chay trong Docker, xuat ra Excel.

## Muc tieu cua tool
1. Cao danh sach video/article public tu `https://community.arc.io/en/public/content`.
2. Doc trang "My Contributions" (sau khi dang nhap, qua cookie) de biet user DA xem cai nao.
3. Tu dong danh dau "Da xem" trong file Excel.
4. De xuat cai chua xem theo quota ngay (4 video + 5 article), in link de copy mo browser.
5. Report/Blacklist link die: user danh dau item loi (link hong/khong xem duoc) ->
   item do bi loai khoi de xuat vinh vien, to xam trong Excel.

## Tinh nang Report / Blacklist
- Cot `Blacklist` trong Excel ("Yes" hoac rong). Menu muc **2. Report link die**:
  hien item dang de xuat hom nay (danh so chung video+article), nhap so (vd `1,3,5`)
  de set Blacklist=Yes. `get_recommendations()` loai bo item blacklist -> khong de xuat lai.
- Bo blacklist: user xoa "Yes" trong cot Blacklist roi luu Excel -> lan chay sau item
  do duoc de xuat binh thuong (sync chi cap nhat Title/URL, KHONG ghi de cot Blacklist).
- Mau Excel: "Da xem" -> xanh (C6EFCE); "Blacklist" -> xam (D9D9D9); uu tien xanh khi trung.

## Kien truc
- `arc_tracker.py` — toan bo logic (scrape, parse, Excel, menu CLI).
- `Dockerfile` / `docker-compose.yml` — dong goi container.
- `config/cookie.txt` — cookie dang nhap (user tu tao tu cookie.txt.example).
- `data/arc-content.xlsx` — file Excel output (mount ra host).
- `data/debug/` — HTML cua trang contributions duoc luu lai khi parse that bai.

## Phan CAN HOAN THIEN tren may that (uu tien lam giup user)

Khi build, tool da test OK phan: scrape regex, parse lich su (theo pattern screenshot),
Excel I/O, dem quota. NHUNG 2 cho sau can verify/chinh voi cookie that:

### 1. URL trang Contributions
Bien `CONTRIB_URLS` trong `arc_tracker.py` dang la danh sach DOAN. Trang "My Contributions"
trong screenshot nam o `community.arc.io/home`. Hay:
- Chay tool 1 lan voi cookie that.
- Neu bao "Khong parse duoc lich su", mo `data/debug/*.html` xem trang co chua data khong.
- Neu HTML rong (chi co shell) -> trang load bang JS/API. Lam buoc 2.

### 2. Neu contributions load bang API (kha nang cao - site dung Gradual/Circle SPA)
Site co the tra content qua JSON API thay vi HTML. Cach tim:
- Tren Chrome (da dang nhap) -> DevTools -> Network -> Fetch/XHR.
- Tai trang contributions, tim request tra ve JSON co title cac content da xem
  (vd endpoint dang `api.gradual.com/...` hoac `community.arc.io/api/...`).
- Copy URL endpoint do, sua ham `fetch_viewed_titles()` de goi thang API + parse JSON.
  JSON se on dinh hon nhieu so voi scrape HTML.

### 3. Anti-bot (neu gap)
Site co the dung Cloudflare. Cookie that copy tu browser thuong da chua `cf_clearance`,
nen request kem cookie + dung User-Agent (giong browser luc lay cookie) thuong qua duoc.
Neu van 403: cho user copy them dung User-Agent cua ho, set vao HEADERS.

## Test nhanh
```bash
# Chay local khong Docker (de debug nhanh)
pip install -r requirements.txt
ARC_DATA_DIR=./data ARC_CONFIG_DIR=./config python3 arc_tracker.py
```

## Nguyen tac
- KHONG hard-code cookie vao code. Luon doc tu file/env.
- Giu logic merge: item da "Da xem" trong Excel khong bi ghi de khi refresh.
