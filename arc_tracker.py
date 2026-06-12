#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Arc House Content Tracker
-------------------------
Theo doi noi dung video/bai viet tren community.arc.io de toi uu diem contribution.

Cach hoat dong (da reverse-engineer tu site that - xem CLAUDE.md):
- Site la Next.js + GraphQL (nen tang Gradual). Endpoint: POST /api/graphql
- Moi request can header chong bot `x-nonce` (HMAC + timestamp) sinh boi JS that
  cua site -> tool goi `nonce_gen.js` (Node) de tao nonce tuoi cho tung request.
- Cookie dang nhap doc tu /config/cookie.txt (KHONG hard-code).
- User-Agent PHAI giong luc lay cookie (cf_clearance gan voi UA) -> dung UA mobile.

Lay du lieu:
- Content public: query getContentPageContents + getPaginatedCollectionPageContents
  (trang chinh + cac collection) -> luu Excel.
- Lich su da xem: query myContributionLogs -> cac log "Watch a Video"/"Read Content"
  co title + ngay that -> tu danh dau "Da xem".
- Lifetime points: query myTenantUser.totalContributionPoints.

Chay trong Docker. Data luu o /data (mount ra host).
"""

import os
import re
import sys
import json
import uuid
import subprocess
import datetime as dt

import requests
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

# ----------------------------- Cau hinh -----------------------------
BASE_URL  = "https://community.arc.io"
GQL_URL   = f"{BASE_URL}/api/graphql"
TENANT_ID = "688b1c42d1f8bff20fcac7a4"   # tenant "Arc House" (public, lay tu __NEXT_DATA__)

# x-client: phải khớp với chuỗi dùng để sinh nonce (server kiểm HMAC theo x-client).
# Giá trị này chỉ cần nhất quán giữa nonce và header; lấy từ build hiện tại của site.
X_CLIENT = os.environ.get(
    "ARC_X_CLIENT",
    "Gradual - v3.99.0-prod-563002e-5330250a3d7d628bf4a80828a6213a8f")

# User-Agent mobile (giống lúc lấy cookie / cf_clearance). Sai UA -> Cloudflare/403.
USER_AGENT = os.environ.get(
    "ARC_USER_AGENT",
    "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/148.0.0.0 Mobile Safari/537.36")

# Cac nguon content can cao (trang chinh + collections)
COLLECTION_SLUGS = ["architects", "stablecoin-101-2025-10-25"]

DATA_DIR    = os.environ.get("ARC_DATA_DIR", "/data")
CONFIG_DIR  = os.environ.get("ARC_CONFIG_DIR", "/config")
APP_DIR     = os.path.dirname(os.path.abspath(__file__))
EXCEL_PATH  = os.path.join(DATA_DIR, "arc-content.xlsx")
DEBUG_DIR   = os.path.join(DATA_DIR, "debug")

# nonce: script Node + file chunk JS (co the bi sua/refresh khi site deploy lai)
NONCE_SCRIPT = os.path.join(APP_DIR, "nonce_gen.js")
CHUNK_VENDOR = os.path.join(APP_DIR, "nonce_chunk.js")        # ban di kem image
CHUNK_DATA   = os.path.join(DATA_DIR, "nonce_chunk.js")       # ban refresh (ghi duoc)

# Quota theo rule Arc
VIDEO_DAILY_MAX   = 4   # 4 diem/video, toi da 4 video/24h
ARTICLE_DAILY_MAX = 5   # 2 diem/bai,   toi da 5 bai/24h
VIDEO_POINTS      = 4
ARTICLE_POINTS    = 2

COLUMNS = ["ID", "Type", "Title", "URL", "Points",
           "Status", "DateAdded", "DateViewed", "Note", "Blacklist"]

# ----------------------------- Tien ich -----------------------------
class C:
    R = "\033[91m"; G = "\033[92m"; Y = "\033[93m"; B = "\033[94m"
    M = "\033[95m"; CY = "\033[96m"; GR = "\033[90m"; W = "\033[0m"; BOLD = "\033[1m"

def today_str():
    return dt.date.today().isoformat()

def norm(s):
    """Chuan hoa text de so khop title."""
    if not s:
        return ""
    s = str(s).lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()

def load_cookie():
    """Doc cookie tu env hoac file. Tra ve chuoi cookie hoac None."""
    env = os.environ.get("ARC_COOKIE", "").strip()
    if env:
        return env
    path = os.path.join(CONFIG_DIR, "cookie.txt")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            val = f.read().strip()
        if val and not val.startswith("#"):
            return val
    return None

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "content-type": "application/json",
        "origin": BASE_URL,
        "referer": f"{BASE_URL}/home/contributors/my-contributions",
        "x-client": X_CLIENT,
        "x-locale": "en",
        "x-tenant-id": TENANT_ID,
    })
    cookie = load_cookie()
    if cookie:
        s.headers["Cookie"] = cookie
    return s, bool(cookie)

# ----------------------------- Nonce chong bot -----------------------------
def _chunk_path():
    return CHUNK_DATA if os.path.exists(CHUNK_DATA) else CHUNK_VENDOR

def gen_nonce(chunk_path=None):
    """Goi Node de sinh x-nonce tuoi tu chinh JS cua site."""
    chunk_path = chunk_path or _chunk_path()
    env = dict(os.environ, ARC_NONCE_CHUNK=chunk_path)
    out = subprocess.check_output(
        ["node", NONCE_SCRIPT, X_CLIENT], env=env, text=True,
        stderr=subprocess.DEVNULL, timeout=30)
    return out.strip()

def refresh_nonce_chunk(session):
    """Tai lai chunk JS chua generateNonce tu site (khi site deploy lai)."""
    try:
        r = session.get(f"{BASE_URL}/home/contributors/my-contributions", timeout=30)
        html = r.text
        srcs = re.findall(r'<script[^>]+src="([^"]+\.js)"', html)
        for u in srcs:
            full = u if u.startswith("http") else BASE_URL + u
            try:
                js = session.get(full, timeout=30).text
            except Exception:
                continue
            if "generateNonce" in js and "36035:function" in js:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(CHUNK_DATA, "w", encoding="utf-8") as f:
                    f.write(js)
                return True
    except Exception as e:
        print(f"{C.R}Khong refresh duoc nonce chunk: {e}{C.W}")
    return False

def ensure_nonce(session):
    """Dam bao sinh duoc nonce; neu khong, thu refresh chunk tu site."""
    try:
        if gen_nonce():
            return True
    except Exception:
        pass
    print(f"{C.Y}Nonce loi -> dang lam moi tu site...{C.W}")
    if refresh_nonce_chunk(session):
        try:
            return bool(gen_nonce(CHUNK_DATA))
        except Exception as e:
            print(f"{C.R}Van loi sau khi refresh: {e}{C.W}")
    return False

# ----------------------------- GraphQL -----------------------------
def gql(session, operation, query, variables):
    """POST 1 query GraphQL voi nonce tuoi. Tra ve dict 'data' hoac raise."""
    headers = {
        "x-request-id": str(uuid.uuid4()),
        "x-session-id": str(uuid.uuid4()),
        "x-nonce": gen_nonce(),
    }
    payload = {"operationName": operation, "query": query, "variables": variables}
    r = session.post(GQL_URL, data=json.dumps(payload), headers=headers, timeout=40)
    try:
        body = r.json()
    except Exception:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    if body.get("errors"):
        raise RuntimeError(body["errors"][0].get("message", "GraphQL error"))
    return body.get("data") or {}

# Chi lay field can thiet (id/slug/title/typename) cho gon
_CONTENT_REC = ("... on Blog { id slug title __typename } "
                "... on LVTenantVideo { id slug title __typename }")

Q_CONTENT_PAGE = (
    "query GetContentPageContents($tenantId: String!, $skip: Int, $limit: Int) {"
    "  contents: getContentPageContents(tenantId: $tenantId, skip: $skip, limit: $limit) {"
    "    totalCount records { %s } } }" % _CONTENT_REC)

Q_COLLECTION = (
    "query GetPaginatedCollectionPageTenantContents($tenantId: String!, $collectionSlug: String!, $skip: Int, $limit: Int) {"
    "  contents: getPaginatedCollectionPageContents(tenantId: $tenantId, collectionSlug: $collectionSlug, skip: $skip, limit: $limit) {"
    "    totalCount records { %s } } }" % _CONTENT_REC)

Q_POINTS = (
    "query MyContributionInfo($tenantId: MongoID!) {"
    "  tenantUser: myTenantUser(tenantId: $tenantId) {"
    "    id totalContributionPoints totalContributionBadgeCount } }")

Q_LOGS = (
    "query MyContributionLogs($tenantId: ID!, $skip: Int, $limit: Int) {"
    "  contributionLogs: myContributionLogs(tenantId: $tenantId, skip: $skip, limit: $limit) {"
    "    id point count roleType logType occurredAt notes"
    "    contributionRole { id name }"
    "    group { ... on Blog { id title } ... on LVTenantVideo { id title }"
    "            ... on ForumPost { id title } ... on Meetup { id name } ... on Club { id name } } } }")

PAGE = 50  # limit toi da server chap nhan

def _record_to_item(rec):
    tp = rec.get("__typename", "")
    slug = rec.get("slug", "")
    title = (rec.get("title") or slug.replace("-", " ").title()).strip()
    if tp == "LVTenantVideo":
        ctype = "Video"; url = f"{BASE_URL}/public/videos/{slug}"
    else:
        ctype = "Article"; url = f"{BASE_URL}/public/blogs/{slug}"
    rid = f"{ctype.lower()}:{slug}"
    return {
        "ID": rid, "Type": ctype, "Title": title, "URL": url,
        "Points": VIDEO_POINTS if ctype == "Video" else ARTICLE_POINTS,
        "Status": "Chua xem", "DateAdded": today_str(),
        "DateViewed": "", "Note": "", "Blacklist": "",
    }

# ----------------------------- Cao content public -----------------------------
def fetch_public_content(session):
    print(f"{C.CY}Dang tai content tu Arc House (trang chinh + collections)...{C.W}")
    items = {}

    def add(recs):
        for rec in recs:
            if not rec.get("slug"):
                continue
            it = _record_to_item(rec)
            items.setdefault(it["ID"], it)

    # 1) Trang content chinh (co pagination)
    skip = 0
    while True:
        d = gql(session, "GetContentPageContents", Q_CONTENT_PAGE,
                {"tenantId": TENANT_ID, "skip": skip, "limit": PAGE}).get("contents")
        if not d:
            break
        recs = d["records"]; add(recs)
        skip += len(recs)
        if not recs or skip >= d["totalCount"]:
            break

    # 2) Cac collection
    for slug in COLLECTION_SLUGS:
        s2 = 0
        while True:
            try:
                d = gql(session, "GetPaginatedCollectionPageTenantContents", Q_COLLECTION,
                        {"tenantId": TENANT_ID, "collectionSlug": slug, "skip": s2, "limit": PAGE}).get("contents")
            except Exception as e:
                print(f"{C.Y}  Collection {slug} loi: {e}{C.W}")
                break
            if not d:
                break
            recs = d["records"]; add(recs)
            s2 += len(recs)
            if not recs or s2 >= d["totalCount"]:
                break

    print(f"{C.G}Tim thay {len(items)} item content.{C.W}")
    return list(items.values())

# ----------------------------- Lich su da xem + points -----------------------------
def fetch_contribution_logs(session):
    """Lay TOAN BO contribution logs (co pagination)."""
    logs = []; skip = 0
    while True:
        arr = gql(session, "MyContributionLogs", Q_LOGS,
                  {"tenantId": TENANT_ID, "skip": skip, "limit": PAGE}).get("contributionLogs")
        if not arr:
            break
        logs += arr; skip += len(arr)
        if len(arr) < PAGE:
            break
    return logs

def fetch_lifetime_points(session):
    try:
        tu = gql(session, "MyContributionInfo", Q_POINTS, {"tenantId": TENANT_ID}).get("tenantUser") or {}
        return tu.get("totalContributionPoints")
    except Exception as e:
        print(f"{C.Y}Khong lay duoc lifetime points: {e}{C.W}")
        return None

def fetch_viewed_titles(session, has_cookie):
    """
    Tra ve dict { title_da_chuan_hoa: ngay_xem } cho cac content user DA xem/doc,
    lay tu myContributionLogs (role 'Watch a Video' / 'Read Content').
    Khong co cookie / loi -> tra ve {}.
    """
    if not has_cookie:
        print(f"{C.Y}Chua co cookie -> bo qua dong bo lich su (xem README).{C.W}")
        return {}
    os.makedirs(DEBUG_DIR, exist_ok=True)
    try:
        logs = fetch_contribution_logs(session)
    except Exception as e:
        print(f"{C.R}Khong doc duoc lich su (GraphQL): {e}{C.W}")
        return {}

    with open(os.path.join(DEBUG_DIR, "contribution_logs.json"), "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

    viewed = {}
    for l in logs:
        role = (l.get("contributionRole") or {}).get("name") or ""
        if role not in ("Watch a Video", "Read Content"):
            continue
        g = l.get("group") or {}
        title = g.get("title") or g.get("name")
        if not title:
            continue
        date = (l.get("occurredAt") or "")[:10]
        k = norm(title)
        if k and (k not in viewed or date > viewed[k]):
            viewed[k] = date
    print(f"{C.G}Doc {len(logs)} log -> {len(viewed)} content da xem/doc.{C.W}")
    return viewed

def apply_viewed(data, viewed):
    """Danh dau Da xem + ngay that. KHONG bao gio reset 'Da xem' khi refresh."""
    vitems = list(viewed.items())
    matched = 0
    for d in data:
        k = norm(d["Title"])
        date = viewed.get(k)
        if date is None:
            for vk, vd in vitems:           # fuzzy: title log la tien to/hau to cua title content
                if len(vk) >= 12 and (vk.startswith(k) or k.startswith(vk)):
                    date = vd; break
        if date:
            d["Status"] = "Da xem"
            d["DateViewed"] = date
            matched += 1
        # neu khong match nhung truoc do da "Da xem" -> giu nguyen (khong downgrade)
    return matched

# ----------------------------- Excel I/O -----------------------------
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        return []
    try:
        wb = load_workbook(EXCEL_PATH)
        ws = wb["Content"]
        rows = []
        headers = [c.value for c in ws[1]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            if r[0] is None:
                continue
            d = {headers[i]: (r[i] if i < len(r) else "") for i in range(len(headers))}
            for col in COLUMNS:
                d.setdefault(col, "")
                if d[col] is None:
                    d[col] = ""
            rows.append(d)
        return rows
    except Exception as e:
        print(f"{C.Y}Khong doc duoc Excel cu ({e}), tao moi.{C.W}")
        return []

def save_excel(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    wb = Workbook()
    ws = wb.active
    ws.title = "Content"

    head_fill = PatternFill("solid", fgColor="1F4E78")
    head_font = Font(bold=True, color="FFFFFF")
    done_fill  = PatternFill("solid", fgColor="C6EFCE")   # xanh la nhat (Da xem)
    black_fill = PatternFill("solid", fgColor="D9D9D9")   # xam nhat (Blacklist)

    ws.append(COLUMNS)
    for i, _ in enumerate(COLUMNS, 1):
        c = ws.cell(row=1, column=i)
        c.fill = head_fill; c.font = head_font
        c.alignment = Alignment(vertical="center")

    # sap xep: chua xem len truoc, moi nhat truoc
    data_sorted = sorted(
        data,
        key=lambda d: (d.get("Status") == "Da xem", d.get("Type", ""), d.get("Title", "")),
    )
    ncol = len(COLUMNS)
    for d in data_sorted:
        ws.append([d.get(c, "") for c in COLUMNS])
        row = ws.max_row
        # Uu tien xanh (Da xem) > xam (Blacklist) > trang (Chua xem chua report)
        fill = None
        if d.get("Status") == "Da xem":
            fill = done_fill                   # TO XANH CA DONG A:J
        elif str(d.get("Blacklist", "")).strip().lower() == "yes":
            fill = black_fill                  # TO XAM CA DONG A:J (da report link die)
        if fill is not None:
            for col in range(1, ncol + 1):
                ws.cell(row=row, column=col).fill = fill

    widths = [30, 9, 52, 48, 7, 10, 12, 12, 16, 10]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    ws.freeze_panes = "A2"
    wb.save(EXCEL_PATH)

# ----------------------------- Sync / merge -----------------------------
def sync(session, has_cookie):
    """Cao content + dong bo lich su. Tra ve (data, logs, points)."""
    existing = load_excel()
    by_id = {d["ID"]: d for d in existing}

    try:
        fresh = fetch_public_content(session)
    except Exception as e:
        print(f"{C.R}Loi cao content: {e}{C.W}")
        fresh = []

    new_count = 0
    for f in fresh:
        if f["ID"] not in by_id:
            by_id[f["ID"]] = f
            new_count += 1
        else:
            by_id[f["ID"]]["Title"] = f["Title"]   # cap nhat title moi nhat
            by_id[f["ID"]]["URL"] = f["URL"]
    data = list(by_id.values())

    logs, points = [], None
    if has_cookie:
        viewed = fetch_viewed_titles(session, has_cookie)
        matched = apply_viewed(data, viewed)
        try:
            logs = fetch_contribution_logs(session)
        except Exception:
            logs = []
        points = fetch_lifetime_points(session)
        if matched:
            print(f"{C.G}Danh dau {matched} item da xem/doc tu lich su that.{C.W}")

    save_excel(data)
    if new_count:
        print(f"{C.G}Them {new_count} item moi.{C.W}")
    return data, logs, points

# ----------------------------- Dashboard / de xuat -----------------------------
def today_log_stats(logs):
    """Tu log THAT cua hom nay: (videos, articles, daily_active, points)."""
    t = today_str()
    vids = arts = daily = pts = 0
    for l in logs:
        if (l.get("occurredAt") or "")[:10] != t:
            continue
        pts += l.get("point") or 0
        role = (l.get("contributionRole") or {}).get("name") or ""
        if role == "Watch a Video":
            vids += 1
        elif role == "Read Content":
            arts += 1
        elif role == "Daily Active":
            daily += 1
    return vids, arts, daily, pts

def dashboard(data, logs, points):
    videos   = [d for d in data if d["Type"] == "Video"]
    articles = [d for d in data if d["Type"] == "Article"]
    vv = sum(1 for d in videos   if d["Status"] == "Da xem")
    av = sum(1 for d in articles if d["Status"] == "Da xem")
    vt, at, daily, pts_today = today_log_stats(logs)

    print()
    print(f"{C.CY}{'='*48}{C.W}")
    print(f"{C.CY}{C.BOLD}        ARC HOUSE CONTENT TRACKER{C.W}")
    print(f"{C.CY}{'='*48}{C.W}")

    print(f"\n{C.Y}LIFETIME{C.W}")
    lp = points if points is not None else "?"
    print(f"  Lifetime points : {C.M}{lp}{C.W}")
    print(f"  Videos          : {vv:3d} / {len(videos):<3d} da xem")
    print(f"  Articles        : {av:3d} / {len(articles):<3d} da doc")

    print(f"\n{C.Y}HOM NAY ({today_str()}){C.W}")
    vc = C.G if vt >= VIDEO_DAILY_MAX else C.W
    ac = C.G if at >= ARTICLE_DAILY_MAX else C.W
    print(f"  {vc}Videos {vt}/{VIDEO_DAILY_MAX}{C.W}  |  "
          f"{ac}Articles {at}/{ARTICLE_DAILY_MAX}{C.W}  |  Daily Active {daily}")
    print(f"  {C.M}Diem hom nay (tu log that): {pts_today}{C.W}")

    vslot = max(0, VIDEO_DAILY_MAX - vt)
    aslot = max(0, ARTICLE_DAILY_MAX - at)
    earnable = vslot * VIDEO_POINTS + aslot * ARTICLE_POINTS
    print(f"\n{C.Y}CON CO THE KIEM{C.W}")
    print(f"  {vslot} video x4 + {aslot} article x2 = {C.G}{earnable} diem{C.W}")

def is_blacklisted(d):
    return str(d.get("Blacklist", "")).strip().lower() == "yes"

def get_recommendations(data, logs):
    """Tinh danh sach de xuat hom nay. Tra ve (videos, articles, vslot, aslot).
    LOAI BO item da blacklist (link die da report) -> khong bao gio de xuat lai."""
    vt, at, _, _ = today_log_stats(logs)
    vslot = max(0, VIDEO_DAILY_MAX - vt)
    aslot = max(0, ARTICLE_DAILY_MAX - at)

    def pick(ctype, slot):
        if slot <= 0:
            return []
        return sorted(
            [d for d in data
             if d["Type"] == ctype and d["Status"] == "Chua xem" and not is_blacklisted(d)],
            key=lambda d: d.get("Title", ""))[:slot]

    return pick("Video", vslot), pick("Article", aslot), vslot, aslot

def recommend(data, logs):
    vids, arts, vslot, aslot = get_recommendations(data, logs)

    print(f"\n{C.Y}DE XUAT HOM NAY{C.W}")
    print(f"{C.GR}{'-'*48}{C.W}")
    if vslot == 0 and aslot == 0:
        print(f"{C.G}Da MAX diem xem/doc hom nay! Quay lai mai.{C.W}")
        return

    if vslot > 0:
        print(f"\n{C.CY}[Video] Con {vslot} slot (4d/cai):{C.W}")
        if not vids:
            print(f"{C.GR}  (Het video chua xem){C.W}")
        for i, d in enumerate(vids, 1):
            print(f"  {i}. {d['Title']}")
            print(f"     {C.B}{d['URL']}{C.W}")

    if aslot > 0:
        print(f"\n{C.CY}[Article] Con {aslot} slot (2d/cai):{C.W}")
        if not arts:
            print(f"{C.GR}  (Het bai chua doc){C.W}")
        for i, d in enumerate(arts, 1):
            print(f"  {i}. {d['Title']}")
            print(f"     {C.B}{d['URL']}{C.W}")

    print(f"\n{C.M}Con co the kiem: {vslot*4 + aslot*2} diem hom nay{C.W}")

def report_dead_links(data, logs):
    """Hien danh sach item dang de xuat hom nay (video + article, danh so chung).
    Cho nhap so (vd '1,3,5') de danh dau Blacklist=Yes -> khong de xuat lai nua."""
    vids, arts, _, _ = get_recommendations(data, logs)
    items = vids + arts   # danh so chung: video truoc, article sau

    print(f"\n{C.Y}REPORT LINK DIE{C.W}")
    print(f"{C.GR}{'-'*48}{C.W}")
    if not items:
        print(f"{C.GR}  (Khong co item nao dang de xuat de report){C.W}")
        return

    for i, d in enumerate(items, 1):
        print(f"  {i}. [{d['Type']}] {d['Title']}")
        print(f"     {C.B}{d['URL']}{C.W}")

    raw = input(f"\nNhap so item link die (vd 1,3,5), Enter de bo qua: ").strip()
    if not raw:
        print(f"{C.GR}Khong report gi.{C.W}")
        return

    picked = set()
    for tok in raw.replace(" ", "").split(","):
        if tok.isdigit():
            n = int(tok)
            if 1 <= n <= len(items):
                picked.add(n)

    n_black = 0
    for n in picked:
        d = items[n - 1]
        if not is_blacklisted(d):
            d["Blacklist"] = "Yes"
            n_black += 1

    if n_black:
        save_excel(data)
        print(f"{C.G}Da blacklist {n_black} item (da luu Excel, se khong de xuat lai).{C.W}")
    else:
        print(f"{C.GR}Khong co item moi nao duoc blacklist.{C.W}")

# ----------------------------- Menu -----------------------------
MENU = f"""
{C.CY}============ MENU ============{C.W}
  1. De xuat hom nay (refresh + dong bo)
  2. Report link die (blacklist)
  3. Dashboard
  0. Thoat
{C.CY}=============================={C.W}"""

def main():
    print(f"{C.CY}Khoi dong Arc House Tracker...{C.W}")
    print(f"{C.GR}Excel: {EXCEL_PATH}{C.W}")
    session, has_cookie = make_session()

    if not ensure_nonce(session):
        print(f"{C.R}Khong sinh duoc x-nonce (can Node + nonce_gen.js). Dung lai.{C.W}")
        return
    if has_cookie:
        print(f"{C.G}Da nap cookie + nonce OK -> dong bo lich su + points.{C.W}")
    else:
        print(f"{C.Y}Chua co cookie -> chi cao content public.{C.W}")

    data, logs, points = sync(session, has_cookie)
    dashboard(data, logs, points)
    recommend(data, logs)

    if not sys.stdin.isatty():
        return

    while True:
        print(MENU)
        c = input("Chon: ").strip()
        if c == "1":
            data, logs, points = sync(session, has_cookie)
            dashboard(data, logs, points)
            recommend(data, logs)
        elif c == "2":
            report_dead_links(data, logs)
        elif c == "3":
            dashboard(data, logs, points)
        elif c == "0":
            print(f"{C.CY}Bye!{C.W}")
            break
        else:
            print(f"{C.R}Lua chon khong hop le.{C.W}")

if __name__ == "__main__":
    main()
