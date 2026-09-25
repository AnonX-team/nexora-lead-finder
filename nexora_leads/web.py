import logging
import os
from flask import Flask, flash, redirect, render_template, request, url_for
from dotenv import load_dotenv

from .database import VALID_STATUSES, connect, lead_stats, search_leads, update_notes, update_status
from .discovery import discover_leads

def create_app():
    load_dotenv()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    app = Flask(__name__)
    app.secret_key = os.environ.get("NEXORA_FLASK_SECRET", "local-nexora-dashboard")

    @app.get("/")
    def index():
        status = request.args.get("status") if request.args.get("status") in VALID_STATUSES else None
        query = request.args.get("q", "").strip()[:100]
        con = connect()
        try:
            return render_template(
                "index.html", leads=search_leads(con, query, status), statuses=VALID_STATUSES,
                selected=status, query=query, stats=lead_stats(con),
            )
        finally:
            con.close()

    @app.post("/discover")
    def discover():
        location = request.form.get("location", "").strip() or os.environ.get("NEXORA_DEFAULT_LOCATION")
        con = connect()
        try:
            leads = discover_leads(con, limit=10, location=location)
        finally:
            con.close()
        flash(f"Saved {len(leads)} new lead(s). No messages were sent.")
        return redirect(url_for("index"))

    @app.post("/leads/<int:lead_id>/status")
    def status(lead_id):
        value = request.form.get("status")
        try:
            con = connect()
            try:
                updated = update_status(con, lead_id, value)
            finally:
                con.close()
            if updated:
                flash(f"Lead {lead_id} marked {value}.")
            else:
                flash("Lead not found.")
        except ValueError:
            flash("Invalid status.")
        return redirect(url_for("index"))

    @app.post("/leads/<int:lead_id>/notes")
    def notes(lead_id):
        con = connect()
        try:
            updated = update_notes(con, lead_id, request.form.get("notes", ""))
        finally:
            con.close()
        if updated:
            flash(f"Notes saved for lead {lead_id}.")
        else:
            flash("Lead not found.")
        return redirect(url_for("index"))
    return app
