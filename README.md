# Gmail Purger

A self-hosted tool that automatically deletes old emails from a configurable
list of senders — permanently, not just to Trash — and gives you a live
dashboard to see what's been cleaned up. Built to run continuously on a
Raspberry Pi as part of a small home lab.

## Why

Certain senders (newsletters, automated receipts, notifications) accumulate
in an inbox forever with no real reason to keep them past a short window.
Rather than unsubscribing or manually cleaning up, this runs a daily check
and permanently removes anything from the target list that's older than a
configurable number of days — while explicitly protecting anything starred
or marked important, regardless of sender or age.

## How it works

```
┌─────────────┐        ┌──────────────┐        ┌─────────────┐
│   worker     │──────▶│  purge_log    │◀──────│  dashboard   │
│ (daily loop) │  write │   .json       │  read  │  (Flask)     │
└─────────────┘        └──────────────┘        └─────────────┘
       │
       ▼
   Gmail (IMAP)
```

Two independent processes, sharing state only through a JSON log file:

- **`worker.py`** — runs on a fixed interval (default: every 24h). Connects
  to Gmail over IMAP, searches each configured sender for messages older
  than the configured threshold, and permanently deletes matches (copies to
  Trash, expunges from the source, then expunges from Trash too — a true
  IMAP delete requires both steps, or the message just gets archived
  instead of removed).
- **`app.py`** — a lightweight Flask dashboard showing last-run status and
  a log of everything deleted. Read-only with respect to Gmail; it never
  touches the mailbox directly, only the log file the worker writes.

This split means the dashboard can restart, crash, or be down entirely
without affecting the purge schedule, and vice versa.

## Features

- Permanent deletion (not just "move to Trash") via a full IMAP
  copy → expunge → expunge sequence
- Protects starred and Gmail-marked-important messages automatically,
  regardless of sender or age
- Searches across all mail (inbox, archived, labeled) rather than just
  the inbox — matches what you'd actually expect from a sender-based
  cleanup rule
- Live dashboard with connectivity status and a running deletion log
- Config-driven target list (`targets.json`) — no code changes needed to
  add or remove senders
- Fully containerized: two services (worker + dashboard) sharing config
  and log data through a mounted volume
- Auto-restarts on failure, survives reboots (`restart: unless-stopped`)

## Setup

### 1. Generate a Gmail App Password

Requires 2-Step Verification enabled on your Google account.
Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
and generate a 16-character app password. This is used instead of your real
password — it can be revoked independently at any time without affecting
your main account credentials.

### 2. Clone and configure

```bash
git clone https://github.com/MariosMoraitis/gmail_bot.git
cd gmail-purger

cp .env.example .env
nano .env   # fill in your Gmail address, app password, purge threshold

cp config/targets.json.example config/targets.json
nano config/targets.json   # your list of sender addresses to purge
```

### 3. Run

```bash
./install.sh
```

Or manually:
```bash
docker compose up -d --build
```

Dashboard will be available at `http://<host>:6000`.

### Useful commands

```bash
docker compose ps                 # container status
docker compose logs -f worker     # watch purge activity live
docker compose logs -f dashboard  # watch the web server
docker compose down               # stop everything
```

## Configuration reference

| Variable                | Default | Description                                  |
|--------------------------|---------|-----------------------------------------------|
| `GMAIL_ADDRESS`           | —       | Your Gmail address                            |
| `GMAIL_APP_PASSWORD`      | —       | 16-character app password                     |
| `PURGE_DAYS`              | `5`     | Delete messages older than this many days     |
| `CHECK_INTERVAL_HOURS`    | `24`    | How often the worker runs a purge cycle       |

`config/targets.json` — a plain JSON array of sender email addresses:
```json
[
  "newsletter@example.com",
  "notifications@another-example.com"
]
```

## Technical notes / things I learned building this

Gmail's IMAP implementation has a few real, non-obvious quirks that broke
this project in ways worth documenting:

- **Standard IMAP `SEARCH` criteria (`FROM`, `BEFORE`) don't reliably match
  what Gmail's own web search finds**, even with correct syntax. Gmail
  provides an extension, `X-GM-RAW`, that accepts the exact same query
  syntax as the Gmail search box (`from:x older_than:5d -is:starred`) and
  is what this project actually uses — it's the only way to get results
  that match what you'd see searching manually.
- **IMAP sequence numbers shift on every expunge.** An early version of
  this project fetched a list of sequence numbers once, then looped through
  them one at a time, deleting as it went — expunging message N shifts
  every subsequent message's position down by one, silently pointing the
  next loop iteration at the wrong message. Fixed by using UID-based
  commands (`conn.uid('SEARCH', ...)`, `conn.uid('STORE', ...)`, etc.)
  throughout — UIDs are stable identifiers that don't shift when other
  messages are removed.
- **A true permanent delete in IMAP isn't a single flag.** Flagging a
  message `\Deleted` and expunging it from its current folder just removes
  it from *that* folder — Gmail keeps it in "All Mail." Genuinely
  permanent deletion requires copying into `[Gmail]/Trash` first, expunging
  the original, then finding the same message inside Trash (matched by
  `Message-ID`, since it gets a new UID there) and expunging it a second
  time.
- **Inbox vs. All Mail matters for search scope.** IMAP `SEARCH` only
  looks inside whichever mailbox is currently `SELECT`ed. A sender whose
  messages had been archived (no longer in Inbox) returned zero results
  when searching `INBOX`, despite Gmail's web search finding them
  immediately — because web search spans all mail by default. Fixed by
  searching `[Gmail]/All Mail` instead of `INBOX`.
- **Folder names are localized.** `[Gmail]/Trash` and `[Gmail]/All Mail`
  aren't guaranteed names — they depend on the account's display language.
  Worth listing folders (`conn.list()`) rather than assuming.

## Architecture decisions

- **Two containers sharing a bind-mounted volume**, rather than one
  process doing everything: keeps the always-on purge logic and the
  request-driven dashboard independently restartable and testable.
- **Environment variables for secrets, JSON files for config/state**:
  credentials never touch the image or the git history; `targets.json`
  and `purge_log.json` are both gitignored, with `.example` versions
  committed to document their shape.
- **App Password + IMAP over OAuth2 + Gmail API**: simpler dependency
  footprint (Python's standard library `imaplib`, no Google SDK), at the
  cost of a less granular, non-scoped credential. A reasonable tradeoff
  for a single-user personal tool; OAuth2 would be the better choice for
  anything multi-user or more security-sensitive.

## Stack

Python · Flask · `imaplib` (standard library) · Docker · Docker Compose

## Disclaimer

This permanently deletes email. Test against a throwaway sender/address
before pointing it at real target addresses, and understand that IMAP
expunge is not undoable — there is no recovery once a message is expunged
from Trash.
