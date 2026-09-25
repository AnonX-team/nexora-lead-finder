import sqlite3
import os
from pathlib import Path

# The launcher used by the Kali package sets NEXORA_DATA_DIR to the user's
# local data directory. The regular source checkout continues to use ./data.
DATABASE_PATH = Path(os.environ.get("NEXORA_DATA_DIR", "data")) / "nexora_leads.sqlite3"
VALID_STATUSES = ("New", "Approved", "Rejected", "Contacted", "Follow-up")
RECON_COLUMNS = {
    "site_title": "TEXT",
    "site_description": "TEXT",
    "https_enabled": "INTEGER NOT NULL DEFAULT 0",
    "security_headers": "TEXT",
    "technology_signals": "TEXT",
    "recon_summary": "TEXT",
}


def connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DATABASE_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("""CREATE TABLE IF NOT EXISTS leads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL, website TEXT NOT NULL,
        website_key TEXT NOT NULL UNIQUE, industry TEXT, location TEXT,
        profile_url TEXT, security_reason TEXT, lead_score INTEGER NOT NULL,
        outreach_message TEXT, status TEXT NOT NULL DEFAULT 'New',
        discovered_on TEXT NOT NULL, source_url TEXT, notes TEXT,
        CHECK (lead_score BETWEEN 1 AND 100),
        CHECK (status IN ('New','Approved','Rejected','Contacted','Follow-up'))
    )""")
    # Keep previously created local databases compatible with newer app versions.
    existing = {row["name"] for row in con.execute("PRAGMA table_info(leads)")}
    for column, definition in RECON_COLUMNS.items():
        if column not in existing:
            con.execute(f"ALTER TABLE leads ADD COLUMN {column} {definition}")
    con.commit()
    return con


def lead_exists(con, website_key):
    return con.execute("SELECT 1 FROM leads WHERE website_key=?", (website_key,)).fetchone() is not None


def add_lead(con, lead):
    cols = list(lead)
    con.execute(f"INSERT INTO leads ({','.join(cols)}) VALUES ({','.join('?' for _ in cols)})", [lead[c] for c in cols])
    con.commit()


def all_leads(con, status=None):
    query, params = "SELECT * FROM leads", []
    if status:
        query += " WHERE status=?"; params.append(status)
    return con.execute(query + " ORDER BY lead_score DESC, id DESC", params).fetchall()


def search_leads(con, query="", status=None):
    """Return leads filtered by status and a small set of review-friendly fields."""
    clauses, params = [], []
    if status:
        clauses.append("status=?")
        params.append(status)
    if query:
        term = f"%{query.strip()}%"
        clauses.append("(company_name LIKE ? OR website LIKE ? OR industry LIKE ? OR location LIKE ?)")
        params.extend([term] * 4)
    statement = "SELECT * FROM leads"
    if clauses:
        statement += " WHERE " + " AND ".join(clauses)
    return con.execute(statement + " ORDER BY lead_score DESC, id DESC", params).fetchall()


def lead_stats(con):
    rows = con.execute("SELECT status, COUNT(*) AS total FROM leads GROUP BY status").fetchall()
    totals = {status: 0 for status in VALID_STATUSES}
    totals.update({row["status"]: row["total"] for row in rows})
    totals["All"] = sum(totals.values())
    return totals


def update_status(con, lead_id, status):
    if status not in VALID_STATUSES: raise ValueError("Invalid lead status")
    cursor = con.execute("UPDATE leads SET status=? WHERE id=?", (status, lead_id))
    con.commit()
    return cursor.rowcount


def update_notes(con, lead_id, notes):
    cursor = con.execute("UPDATE leads SET notes=? WHERE id=?", (notes.strip()[:2_000], lead_id))
    con.commit()
    return cursor.rowcount
