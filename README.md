# Nexora Lead Finder (V1)

A deliberately small, local lead-generation assistant for Nexora Cyber Tech. It finds up to ten **new** companies per run using public web search results and public company pages, then saves them in SQLite for manual review.

It does not send messages, log in to websites, save passwords, crawl login-only pages, scan for vulnerabilities, or run intrusive tests. Scores describe public business-fit signals only; they are never security findings.

## What you can do

- Find up to ten new companies per run from public search results.
- Filter leads by status or search their company, industry, website, and location.
- Review an explainable 1–100 priority score and a manually-sendable message draft.
- View a passive public website footprint: homepage title/description, HTTPS, public technology keywords, and response-header presence.
- Mark leads Approved, Rejected, Contacted, or Follow-up, and store private review notes.

## Components

| Component | Purpose |
| --- | --- |
| `main.py` | Starts the local Flask dashboard. |
| `nexora_leads/database.py` | Creates and reads the local SQLite schema; prevents duplicate website domains. |
| `nexora_leads/discovery.py` | Searches publicly indexed results and reads normal public HTML pages only. |
| `nexora_leads/scoring.py` | Applies simple, explainable 1–100 business-priority rules. |
| `nexora_leads/messaging.py` | Produces a short, professional draft message. |
| `nexora_leads/web.py` | Dashboard routes for discovery, review status, notes, search, and summary counts. |
| `nexora_leads/templates/index.html` | Local review dashboard. |

## Data flow

```text
Public search → public homepage metadata/text → domain duplicate check
    → score + outreach draft → SQLite → local review dashboard
```

The database is created automatically at `data/nexora_leads.sqlite3`. A normalized website domain has a unique constraint, so a previously stored company site cannot be selected again.

## Setup

Requires Python 3.10+.

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
python main.py
```

Open `http://127.0.0.1:5000` in your browser. Select **Discover up to 10 new leads**, optionally adding a city/country market. Results start with `New`; use the dashboard to mark suitable prospects `Approved` or `Rejected`. V1 has no send function, by design.

## Stored fields

Each record includes company name, website, industry, visible/public location when available, a public LinkedIn/Facebook profile link found on the company site, the reason for fit, 1–100 score, outreach draft, workflow status, and discovery date. It also keeps the public search-result URL for traceability.

## Configuration and safeguards

`.env` is optional. `NEXORA_DEFAULT_LOCATION` sets a preferred market and `NEXORA_HOST`/`NEXORA_PORT` are reserved for local server configuration. V1 does not require an API key and never stores social credentials.

Only use this for legitimate B2B research. The website footprint reads a normal public homepage response only; it does not scan, probe, enumerate, authenticate to, or test a target. Review business relevance and all outreach manually, and follow applicable privacy, anti-spam, and platform rules.

## Kali Linux installer

The package must be built on Kali Linux (or another amd64 Debian-based Linux host), because the executable is platform-specific. On Kali, run:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip dpkg-dev xdg-utils
cd nexoraagent
chmod +x packaging/kali/build-deb.sh
./packaging/kali/build-deb.sh
sudo apt install ./dist/nexora-lead-finder_1.0.0_amd64.deb
```

Open **Nexora Lead Finder** from the applications menu, or run `nexora-lead-finder`. The app opens locally at `http://127.0.0.1:5000` and stores its database in your Linux user data directory.
