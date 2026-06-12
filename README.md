🇬🇧 English | [🇻🇳 Tiếng Việt](README_VI.md)

# 🏛️ Arc House Content Tracker

> A tool to **maximize your contribution points** on [community.arc.io](https://community.arc.io):
> it scrapes every video/article, knows **which ones you've already watched/read**, and suggests **what to watch today** to hit your daily quota.

![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Runs entirely inside **Docker** — spin it up when you need it, close it when you're done, your data stays on your machine. Output is a **color-coded Excel file** that's easy to scan.

---

## ✨ Features

- 📥 **Scrapes all Arc House content** (currently ~**141 items**: videos + articles) into one Excel file.
- ✅ **Auto-marks what you've seen** — reads your real contribution history via GraphQL, no manual ticking.
- 📊 **Dashboard** showing your **lifetime points**, watched/read progress, and today's quota.
- 🎯 **Optimal daily recommendations** (4 videos × 4pts + 5 articles × 2pts = **27 pts/day**) — prints ready-to-copy links.
- 🚫 **Report dead links → blacklist**: hit a broken link once and the tool **never recommends it again**.
- 🎨 **Color-coded Excel**: 🟩 green row = viewed, ⬜ grey row = blacklisted → tell at a glance.
- 🌐 **Bilingual UI** — pick **English** or **Vietnamese** on first run.

---

## 📋 Requirements

| What | Notes |
|------|-------|
| 🐳 **Docker Desktop** | Free download at <https://www.docker.com/products/docker-desktop/> |
| 👤 **A community.arc.io account** | You must be able to log in via your browser (usually with Google/Gmail) |

> No need to install Python or any libraries — Docker handles everything.

---

## 🚀 Setup — step by step for newcomers

### Step 1 — Install Docker Desktop

1. Go to <https://www.docker.com/products/docker-desktop/> → download the **Windows** build.
2. Run the installer, click Next through to the end, restart if prompted.
3. Open **Docker Desktop** (find it in the Start Menu). The first launch takes ~1 minute.
4. Wait until the **whale icon 🐳 in the bottom-right turns green** ("Docker Desktop is running"). You're ready.

> ⚠️ Docker Desktop **must be running** (green icon) every time you use the tool.

### Step 2 — Get the code

Pick **one** of two ways:

**Option A — Download ZIP (easiest, no Git needed):**
1. On the project's GitHub page → click the green **`< > Code`** button → **Download ZIP**.
2. Unzip it. Move/rename the folder to: **`C:\arc-house-community-tool`**

**Option B — Use Git (if installed):**
```powershell
git clone https://github.com/cudencuibap/ARC-HOUSE-CONTENT-TRACKER.git C:\arc-house-community-tool
```

### Step 3 — Get your login cookie

👉 This is the most important step — read the **[⭐ Getting your cookie](#-getting-your-cookie-most-important)** section below carefully.

### Step 4 — Run the tool

- **Easiest:** open `C:\arc-house-community-tool` and **double-click `run.bat`**.
  - The first run builds the image (1–2 min). After that it goes straight to the menu.
- **Or** run from PowerShell:
  ```powershell
  cd C:\arc-house-community-tool
  docker compose run --rm arc-tracker
  ```
- On the **first run** the tool asks you to choose **English / Tiếng Việt** and remembers it.

---

## ⭐ Getting your cookie (MOST IMPORTANT)

### 🤔 Why is a cookie needed?

- The tool needs to know **which content you've already seen** so it won't suggest it again.
- That info lives on your **"My Contributions"** page — your **personal** page.
- A personal page is only accessible **when you're logged in**.
- A **cookie** is like a "sticker" on your browser that tells Arc House *"I'm the person who just logged in."* Hand that cookie to the tool → it can read your personal page for you.

> Without a cookie the tool still runs, but it only scrapes public content and **can't auto-mark what you've watched**.

### ⚠️ Is this safe? (please read)

- ✅ The cookie stays **ONLY** in `config/cookie.txt` **on your machine**. It is **never** sent to any server of this tool, **not to the author**, not to Claude/any AI.
- ✅ The tool is **open-source** — anyone can read `arc_tracker.py` and verify the cookie is used **only** to call **Arc House's own API**, nowhere else.
- ✅ A cookie is **NOT** your Gmail/Google password. Grabbing it **does not expose your password**.
- ✅ `config/cookie.txt` is excluded by `.gitignore` → when you push your code to your own GitHub, **the cookie is NOT pushed along with it**.
- ✅ Cookies **expire** after a few days/weeks. When they do, just copy a fresh one.
- ✅ You can **revoke it anytime**: simply **log out** of community.arc.io in your browser and the old cookie becomes useless.
- ❌ **DON'T** share your cookie or paste it into public forums/groups. Whoever holds it can sign in to **your Arc account** (but **not** your Gmail).
- ❌ **DON'T** commit `config/cookie.txt` to a public GitHub repo (the `.gitignore` already protects you — don't remove that line).

### 🍪 How to get the cookie — step by step

1. Open **Chrome** (or Edge), go to <https://community.arc.io> and **log in** with Gmail as usual.
2. Open your personal history page: <https://community.arc.io/home/contributors/my-contributions>
3. Press **`F12`** to open **DevTools**, select the **`Network`** tab.
4. In the Network filter bar, click the **`Doc`** filter (document type — not Media/JS/CSS).
5. Press **`F5`** to reload. In the request list that appears, **click the first request** (usually matches the page name).
6. The right panel opens → **`Headers`** tab → scroll to **`Request Headers`** → find the line starting with **`cookie:`**
7. **Select the entire** long value after `cookie:` → right-click **Copy value** (or `Ctrl+C`).
8. Open **Notepad**, **paste** it (a **single line**, no line breaks), then **Save** as:
   ```
   C:\arc-house-community-tool\config\cookie.txt
   ```
   > Tip: the `config` folder already has a `cookie.txt.example` template walking through these steps.

🔧 **About User-Agent:** the tool automatically uses the right User-Agent to match your cookie — **you don't need to do anything**.

---

## 🕹️ Usage

On launch the tool auto-refreshes + syncs + shows the dashboard + recommendations, then opens a **3-item menu**:

| Key | Action | When to use |
|-----|--------|-------------|
| **1** | 🎯 **Today's recommendations** | Re-scrapes content, syncs your watch history, prints what to watch today (videos first — 4pts > 2pts). Press `1` again after watching to update. |
| **2** | 🚫 **Report dead links** | Hit a broken/unviewable link — shows the current recommendations, enter numbers (e.g. `1,3,5`) → the tool **blacklists** them and won't suggest them again. |
| **3** | 📊 **Dashboard** | Quick view of lifetime points, how much you've watched/read, and today's remaining slots. |
| **0** | 🚪 **Exit** | Close the tool. Your data stays on your machine. |

**Suggested daily routine:**
1. Run `run.bat` → read the **Recommendations**.
2. Copy a link → open it in Chrome → watch/read.
3. Press `1` to sync (the item you just watched gets auto-marked from real history).
4. Broken link? Press `2` to report it.
5. Out of quota → press `0` to exit.

> 🚫 **Un-blacklist:** open `data/arc-content.xlsx`, delete `Yes` in the **Blacklist** column of that row, save → it gets recommended again next run.

### 🌐 Switching language (English / Vietnamese)

On the **first run** the tool asks you to pick **English / Tiếng Việt**, saves it to `config/language.txt`, and **won't ask again**. To switch language: **delete `config/language.txt`** → the tool will ask again on the next run.

---

## 🛟 Troubleshooting

| Symptom | Fix |
|---------|-----|
| **"Docker not running" / connection error** | Open **Docker Desktop**, wait for the 🐳 icon to turn green, try again. |
| **Watch history not syncing** | Your cookie **expired** → redo [Getting your cookie](#-getting-your-cookie-most-important) with a fresh one. |
| **"Content scrape error" / network error** | Check your **internet**, retry in a few seconds. |
| **403 / Forbidden error** | Cookie **doesn't match the User-Agent** or was revoked → grab a fresh cookie from DevTools (per the steps above). |

---

## 🗂️ Project structure

```
arc-house-community-tool/
├── run.bat                   <- double-click to run (Windows)
├── arc_tracker.py            <- all logic (scrape, parse, Excel, menu, i18n)
├── nonce_gen.js              <- generates anti-bot header (runs via Node in Docker)
├── nonce_chunk.js            <- site JS used for the nonce
├── Dockerfile                <- image recipe
├── docker-compose.yml        <- container run config
├── requirements.txt          <- Python deps
├── README.md / README_VI.md  <- this file (EN / VI)
├── CLAUDE.md / CLAUDE_VI.md  <- technical notes for AI agents (EN / VI)
├── LICENSE                   <- MIT license
├── config/
│   ├── cookie.txt.example    <- cookie how-to
│   ├── cookie.txt            <- (you create) login cookie — NEVER pushed to GitHub
│   └── language.txt          <- (auto) saved UI language: en/vi
└── data/
    ├── arc-content.xlsx      <- Excel output (created on run)
    └── debug/                <- JSON logs for debugging
```

> 📦 Data lives in `data/` **on your machine** → closing the container won't lose it. You can put this folder in OneDrive to sync across machines.

---

## 🤝 Contributing

Very welcome! To improve the tool: fork the repo, create a new branch, commit your changes, then open a **Pull Request** describing what you changed and why. Report bugs/ideas via an **Issue**. Please **don't** attach cookies or personal data in issues/PRs.

---

## 📄 License

Released under the **MIT** license — see [LICENSE](LICENSE). Free to use, modify, and share.

Built by **cudencuibap**. 🏛️

---

> ℹ️ The personal-history reader is built on Arc House's real GraphQL API. The site may change its structure / redeploy → occasionally minor tweaks are needed. See `CLAUDE.md` if you want to use **Claude Code** for quick maintenance.
