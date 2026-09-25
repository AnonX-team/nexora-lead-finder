import tempfile
import unittest
from pathlib import Path

from nexora_leads import database
from nexora_leads.web import create_app


class LeadFinderTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.original_path = database.DATABASE_PATH
        database.DATABASE_PATH = Path(self.temp_dir.name) / "leads.sqlite3"
        self.app = create_app().test_client()
        self.con = database.connect()
        database.add_lead(self.con, {
            "company_name": "Acme Apps", "website": "https://acme.example", "website_key": "acme.example",
            "industry": "SaaS", "location": "Karachi", "profile_url": None, "security_reason": "Public signal",
            "lead_score": 75, "outreach_message": "Hello", "status": "New", "discovered_on": "2026-09-25",
            "source_url": "https://search.example", "notes": None,
            "site_title": "Acme", "site_description": None, "https_enabled": 1,
            "security_headers": "HSTS", "technology_signals": "React", "recon_summary": "HTTPS homepage.",
        })

    def tearDown(self):
        self.con.close()
        database.DATABASE_PATH = self.original_path
        self.temp_dir.cleanup()

    def test_dashboard_search_and_review_updates(self):
        self.assertIn(b"Acme Apps", self.app.get("/?q=Karachi").data)
        self.assertEqual(self.app.post("/leads/1/status", data={"status": "Approved"}).status_code, 302)
        self.assertEqual(database.all_leads(self.con)[0]["status"], "Approved")
        self.app.post("/leads/1/notes", data={"notes": "Strong fit"})
        self.assertEqual(database.all_leads(self.con)[0]["notes"], "Strong fit")


if __name__ == "__main__":
    unittest.main()
