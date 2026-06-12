🇬🇧 English | [🇻🇳 Tiếng Việt](CLAUDE_VI.md)

# CLAUDE.md — Agent guide (Arc House Content Tracker)

> Guide for an **AI agent** (Claude Code, Cursor, …) when a user clones this repo and asks
> for help to set up / use / maintain the tool. Read this file to grasp the architecture and
> the common tasks. Technical terms are kept in English.

---

## 1. Project overview

A tool that tracks content on **community.arc.io** to maximize contribution points: it scrapes
all public videos/articles, reads the user's "viewed" history via GraphQL, auto-marks it, and
recommends what to watch today within the quota (4 videos + 5 articles = 27 pts/day). Output is a
color-coded Excel file. The primary user is Vietnamese, on Windows, running via Docker.

**Tech stack:** Python 3.12 · Docker / docker-compose · `requests` (HTTP) · `openpyxl`
(Excel) · GraphQL (Arc's API) · Node.js (only to generate `x-nonce`).

---

## 2. File architecture

| File | Role |
|------|------|
| `arc_tracker.py` | **All logic**: GraphQL scrape, parse, merge, Excel I/O, CLI menu, i18n. Entrypoint. |
| `Dockerfile` | `python:3.12-slim` image + installs Node.js (for the nonce). Only COPYs `arc_tracker.py`, `nonce_gen.js`, `nonce_chunk.js`. |
| `docker-compose.yml` | Service `arc-tracker`; mounts `./data` → `/data`, `./config` → `/config`; `stdin_open`+`tty` so the menu works. |
| `requirements.txt` | `requests`, `openpyxl`, `beautifulsoup4`. |
| `run.bat` | Windows launcher — double-click to `docker compose run`. |
| `nonce_gen.js` | Node script that takes `x-client`, calls a function in `nonce_chunk.js` → prints `x-nonce` to stdout. |
| `nonce_chunk.js` | JS bundle extracted from the site, contains `generateNonce`. Ships with the image; refreshed copy written to `/data/nonce_chunk.js`. |
| `config/cookie.txt` | **User-created** login cookie. **gitignored** — never commit. |
| `config/cookie.txt.example` | Template explaining how to get the cookie (safe to commit). |
| `config/language.txt` | Saved UI language (`en`/`vi`), auto-created on first run. Personal config, not secret. |
| `data/arc-content.xlsx` | Excel output. **gitignored** (only `data/.gitkeep` is kept). |
| `data/debug/*` | JSON dumps for debugging (e.g. `contribution_logs.json`). **gitignored.** |

---

## 3. Key technical knowledge

- **Platform:** community.arc.io runs on **Gradual/Circle** — a Next.js SPA, data fetched via **GraphQL**.
- **Endpoint:** `POST https://community.arc.io/api/graphql`. The "Arc House" tenant id is in `TENANT_ID`.
- **Auth (see `make_session()` + `gql()`):**
  - `Cookie` — from `config/cookie.txt` (holds the session + Cloudflare `cf_clearance`). The session token lives inside the cookie; there is **no** separate Bearer header.
  - `x-client` — the site's build version string (`X_CLIENT`); the server checks an HMAC against it, so it must **match** the string used to generate the nonce.
  - `x-nonce` — anti-bot token, **regenerated per request** via Node: `gen_nonce()` → runs `nonce_gen.js` with `nonce_chunk.js`.
- **Cloudflare:** the `cf_clearance` in the cookie is **bound to the User-Agent**. `USER_AGENT` in the code **must match** the browser UA used when the cookie was captured, otherwise → **403**.
- **Viewed history:** query `MyContributionLogs` (see `Q_LOGS`) → filter `contributionRole.name` ∈ {`Watch a Video`, `Read Content`} → take `group.title` + `occurredAt`. Data page: `/home/contributors/my-contributions`.
- **Lifetime points:** query `myTenantUser.totalContributionPoints` (`Q_POINTS`).
- **Public content:** `getContentPageContents` (main page, paginated) + `getPaginatedCollectionPageContents` for each slug in `COLLECTION_SLUGS`.
- All secrets/UA/x-client can be overridden via **env** (`ARC_COOKIE`, `ARC_USER_AGENT`, `ARC_X_CLIENT`).

---

## 4. Common user requests (agent templates)

### 4.1. "Help me set up the tool for the first time"
1. Verify Docker Desktop is running: `docker info` (error → tell user to open Docker Desktop, wait for the 🐳 icon to go green).
2. Check the cookie: `Test-Path config/cookie.txt`. Missing → guide 4.2 (still runs, but no history sync).
3. `docker compose build`
4. `docker compose run --rm arc-tracker`

### 4.2. "My cookie expired, help me get a new one"
Guide the user (the agent **can't** do this — it needs the user's browser):
DevTools (`F12`) → **Network** tab → **Doc** filter → `F5` → click the first request →
**Request Headers** → copy the entire value after `cookie:` → overwrite `config/cookie.txt` (single line).
**DON'T** echo/print the cookie contents to the terminal; **DON'T** commit the file.

### 4.3. "Tool returns 403/401 even with a fresh cookie"
Common cause: `USER_AGENT` in `arc_tracker.py` **doesn't match** the browser UA used when the user grabbed the cookie (`cf_clearance` is bound to the UA). Ask the user for their real UA (DevTools → request header `user-agent`), then fix the `USER_AGENT` constant (or set env `ARC_USER_AGENT`). Secondary: cookie missing `cf_clearance` → have them re-copy from the same tab that already passed Cloudflare.

### 4.4. "Tool reports a GraphQL nonce error"
`nonce_chunk.js` is site JS containing `generateNonce`. A site redeploy → the function / `x-client` changes.
The code already has `refresh_nonce_chunk()` which auto-downloads a new bundle when `gen_nonce()` fails. If it still
errors: dump the new JS bundle from DevTools → Network (the `.js` file containing `generateNonce` + `36035:function`),
re-extract it, overwrite `nonce_chunk.js`, and update `X_CLIENT` to match the new build.

### 4.5. "Add a new collection URL to scrape"
In `arc_tracker.py`, add the slug to the **`COLLECTION_SLUGS`** list. `fetch_public_content()` iterates each slug
through `getPaginatedCollectionPageContents`. The slug comes from the collection's URL on the site.

### 4.6. "I changed the code, rebuild it"
```powershell
docker compose build
docker compose run --rm arc-tracker
```

### 4.7. "Push the update to GitHub"
```powershell
git status                            # verify cookie/data do NOT appear
git ls-files | Select-String cookie   # should only show cookie.txt.example
git add .
git commit -m "..."
git push
```

---

## 5. Rules the agent MUST follow

- ⚠️ **NEVER commit/push** `config/cookie.txt`, `data/arc-content.xlsx`, `data/debug/*`.
  **Verify `git ls-files` before every commit** (only `cookie.txt.example` is allowed to appear).
- **Never hard-code** the cookie/token in code — always read from `config/cookie.txt` or env.
- **Don't break state-keeping logic:** on refresh, an item already `"Da xem"` must not be reset; the `Blacklist`
  column the user edits by hand (clearing `"Yes"`) must be respected — `sync()` only updates Title/URL, never touches Status/Blacklist.
- When the user pastes a cookie or a cURL containing one: handle it **purely in local code**, **NEVER** echo/log/print the cookie to the terminal.
- Arc's site may change its API/Cloudflare policy at any time → when something breaks, re-derive from the **user's DevTools dump** (don't guess).

---

## 6. Excel data structure

10 columns: `ID, Type, Title, URL, Points, Status, DateAdded, DateViewed, Note, Blacklist`.

- `Type`: `Video` | `Article`. `Points`: 4 (video) | 2 (article).
- `Status`: `"Chua xem"` | `"Da xem"`.
- `Blacklist`: `"Yes"` | empty (blacklisted items never appear in recommendations).
- **Coloring (in `save_excel()`):** `Da xem` → fill **C6EFCE** (green) across the row; `Blacklist=Yes` → fill **D9D9D9** (grey). **Green wins** if a row is both `Da xem` and `Blacklist`.

---

## 7. Tool menu (3 items)

| Key | Action |
|-----|--------|
| 1 | **Today's recommendations** — `sync()` (scrape + history sync + points) then print optimal links. |
| 2 | **Report dead links** — show recommended items, enter numbers (e.g. `1,3,5`) → set `Blacklist=Yes`. |
| 3 | **Dashboard** — lifetime points + progress + today's quota (read from the real contribution log). |
| 0 | Exit. |

> Note: the menu only runs with a TTY (`sys.stdin.isatty()`); in non-TTY (CI/pipe) the tool prints the dashboard+recommendations once and exits.

---

## 8. i18n (EN/VI) — IMPORTANT when editing text

- **All UI strings** live in the dict `TRANSLATIONS = {"en": {...}, "vi": {...}}`. Read them via `t(key, **kwargs)` (falls back to `en` if a key is missing). **Never hard-code** a new display string — add the key to **both** languages.
- The global `LANG` is set by `select_language()` at startup: it reads `config/language.txt` (`en`/`vi`); if missing and a TTY is present → prompt the user and save; non-TTY → default `en`. The user switches language by **deleting `config/language.txt`**.
- ⚠️ **INTERNAL vs DISPLAY (don't break this):** values stored in Excel are always **internal, fixed Vietnamese** — `Status` = `"Chua xem"`/`"Da xem"`, `Blacklist` = `"Yes"`, `Type` = `"Video"`/`"Article"`. **Never** translate these on load/save → old data stays 100% compatible. Translation happens **only when printing to the terminal** (e.g. helper `status_display()` maps to `t("status_viewed")`).
- `config/language.txt` is personal UI config (not a secret). No need to commit it; each machine generates it on first run.
