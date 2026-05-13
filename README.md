# Jarvis — Personal Engineering Assistant

A self-hosted assistant that hunts for hackathons, networking events, and engineering opportunities so you don't miss them. Runs on a schedule, stores everything in a local database, and pings your phone.

> I built this as a learning project to get hands-on with web scraping, databases, scheduling, and eventually voice I/O and a physical device.

---

## The Problem

- Easy to miss hackathons, networking events, and competitions unless you're constantly checking
- Motivation to apply and track opportunities drops when it feels like manual work
- Wanted something always-on that surfaces opportunities automatically and keeps the excitement alive

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Jarvis                               │
│                                                             │
│  Scrapers          Database         Notifications           │
│  ─────────         ────────         ─────────────           │
│  devpost.py  ───►  lucky.db  ◄───   notifier.py             │
│  ieee.py     ───►  (SQLite)         (ntfy.sh)               │
│                        ▲                                    │
│  Orchestrator          │                                    │
│  ─────────────         │                                    │
│  run.py  ──────────────┘                                    │
│  Task Scheduler (7am daily)                                 │
└─────────────────────────────────────────────────────────────┘
```

**Current stack:** Python · Playwright · BeautifulSoup4 · SQLite · pandas · ntfy.sh

---

## Current Features

| Feature | File | Status |
|---|---|---|
| Scrape Devpost for online hackathons | `devpost_scraper.py` | Working |
| Scrape IEEE UoA Linktree for events | `ieee_scraper.py` | In progress |
| Store events in local SQLite database | `database.py` | Working |
| Push notification to phone on run complete | `notifier.py` | Working |
| Daily run at 7am with structured logging | `run.py` | Working |

### Scrapers

**Devpost** (`devpost_scraper.py`) — Scrapes upcoming online hackathons. Uses a headless Chromium browser (Playwright) to handle infinite scroll and Vue.js rendering, then parses the HTML with BeautifulSoup. Stores: title, URL, start/deadline dates, themes, location.

**IEEE UoA** (`ieee_scraper.py`) — Reads the IEEE University of Auckland Linktree page to find event sign-up links. Currently retrieves all links — filtering for event-only links is a TODO.

### Notifications

Uses [ntfy.sh](https://ntfy.sh) — a free, open-source push notification service. Install the ntfy app on your phone, subscribe to your private topic, and Jarvis will send you a summary after every run.

### Logging

Each run writes a dated log to `logs/lucky_YYYY-MM-DD.log`:

```
2026-05-08 07:00:01 [INFO] ============================================================
2026-05-08 07:00:01 [INFO] Lucky run started - 2026-05-08 07:00:01
2026-05-08 07:00:01 [INFO] [devpost] Starting scraper...
2026-05-08 07:00:24 [INFO] [devpost] Done - 48 tiles found in 23.1s
2026-05-08 07:00:24 [INFO] ------------------------------------------------------------
2026-05-08 07:00:24 [INFO] Run finished in 23.2s
2026-05-08 07:00:24 [INFO]   Tiles found : 48
2026-05-08 07:00:24 [INFO]   Scrapers run: 1
2026-05-08 07:00:24 [INFO]   Errors      : none
2026-05-08 07:00:24 [INFO] ============================================================
```

---

## Setup

### 1. Clone and create a virtual environment

```powershell
git clone <repo-url>
cd web_scraper
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure environment variables
create an env file.

```env
NTFY_TOPIC=your-private-topic-name
```

To get a topic: install the [ntfy app](https://ntfy.sh), create a topic name (treat it like a password — anyone who knows it can subscribe).

### 3. Initialise the database

```powershell
python database.py
```

### 4. Run manually

```powershell
python run.py
```

### 5. Schedule daily runs (Windows Task Scheduler)

The `scheduler.py` file sets up a 7am daily trigger. Run it once to register the task:

```powershell
python scheduler.py
```

---

## Project Roadmap

### Phase 1 — Information Gathering (current)
- [x] Scrape Devpost for hackathons
- [x] SQLite database for deduplication and storage
- [x] Phone push notifications via ntfy
- [x] Structured daily logging
- [ ] Filter IEEE scraper to event sign-ups only
- [ ] Add Eventbrite / Meetup scrapers (Auckland events)
- [ ] Scrape university tech club Instagram pages (SESA, WDCC, GDCC, StartUp Club)
- [ ] Deduplicate new vs. already-seen events in the database
- [x] Strip events where the start date has already passed

### Phase 2 — Smarter Notifications
- [ ] Only notify about genuinely new events (not re-scraped duplicates)
- [ ] Weekly digest summary
- [ ] Calendar integration — add events automatically to Google Calendar

### Phase 3 — Physical Device
- [ ] Port to Raspberry Pi (always-on, off personal laptop)
- [ ] Voice interface with Jarvis-style TTS
- [ ] Wake word detection
- [ ] Camera module for future projects

---

## Adding a New Scraper

1. Create `your_source_scraper.py` with a `scrape_your_source() -> dict` function that returns `{"scraper": "name", "total_found": int}`.
2. Register it in `run.py`:

```python
from your_source_scraper import scrape_your_source

SCRAPERS = [
    ("devpost", scrape_devpost),
    ("your_source", scrape_your_source),  # add here
]
```

That's it — the orchestrator handles timing, logging, error isolation, and notifications automatically.

---

## File Structure

```
web_scraper/
├── run.py                 # Orchestrator — runs all scrapers daily
├── devpost_scraper.py     # Scrapes Devpost hackathons
├── ieee_scraper.py        # Scrapes IEEE UoA Linktree events
├── database.py            # SQLite schema and queries
├── notifier.py            # Phone push notifications (ntfy.sh)
├── lucky.db               # SQLite database (git-ignored)
├── requirements.txt       # Python dependencies
├── .env                   # Secrets — never commit this
├── .env.example           # Template for .env
└── logs/                  # Daily run logs (git-ignored)
```
