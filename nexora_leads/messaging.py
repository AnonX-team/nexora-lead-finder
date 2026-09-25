def draft_message(company_name, reason, recon_summary=None):
    concise_reason = reason.replace("Public information suggests ", "").replace(" This is not a security finding.", "")
    recon_line = ""
    if recon_summary:
        recon_line = " I also reviewed only the information publicly returned by your homepage; no testing was performed."
    return (f"Hi {company_name} team,\n\nI came across your public website and noticed {concise_reason} "
            f"{recon_line} Nexora Cyber Tech helps growing businesses strengthen web applications and APIs through practical security reviews. "
            "Would a brief conversation about your application-security priorities be useful?\n\nBest,\nNexora Cyber Tech")
