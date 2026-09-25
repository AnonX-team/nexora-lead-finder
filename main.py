"""Start Nexora's local lead-review dashboard."""
import os
from nexora_leads.web import create_app

if __name__ == "__main__":
    create_app().run(
        host=os.environ.get("NEXORA_HOST", "127.0.0.1"),
        port=int(os.environ.get("NEXORA_PORT", "5000")),
        debug=False,
    )
