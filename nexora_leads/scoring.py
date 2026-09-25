"""Explainable priority scoring. Scores are not vulnerability findings."""

def score_lead(text, industry):
    text = text.lower()
    score, signals = 42, []
    rules = [
        (("api", "integration", "developer portal"), 18, "public-facing APIs or integrations"),
        (("e-commerce", "ecommerce", "checkout", "payment", "shop"), 16, "online transactions or customer data"),
        (("saas", "platform", "dashboard", "cloud"), 14, "an internet-facing software platform"),
    ]
    for words, points, signal in rules:
        if any(word in text for word in words): score += points; signals.append(signal)
    if industry in {"Software services", "Web development agency", "Digital agency"}:
        score += 9; signals.append("multiple client-facing web applications")
    if not signals: signals.append("an active public website that could benefit from a proactive security review")
    return min(score, 100), "Public information suggests " + ", ".join(signals) + ". This is not a security finding."
