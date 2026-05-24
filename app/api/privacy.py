from datetime import date

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["Legal"])

LAST_UPDATED = date(2026, 5, 25).isoformat()

PRIVACY_HTML = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Privacy Policy — Live in a Week</title>
  <style>
    :root {{
      color-scheme: light dark;
      --fg: #1a1a1a;
      --muted: #555;
      --bg: #fafafa;
      --card: #fff;
      --border: #e5e5e5;
      --accent: #2563eb;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --fg: #ededed;
        --muted: #a0a0a0;
        --bg: #0f0f10;
        --card: #18181b;
        --border: #2a2a2e;
        --accent: #60a5fa;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Inter, sans-serif;
      background: var(--bg);
      color: var(--fg);
      line-height: 1.6;
    }}
    main {{
      max-width: 760px;
      margin: 0 auto;
      padding: 48px 24px 96px;
    }}
    h1 {{ font-size: 2rem; margin: 0 0 4px; }}
    h2 {{ font-size: 1.25rem; margin: 32px 0 8px; }}
    .meta {{ color: var(--muted); font-size: 0.9rem; margin-bottom: 32px; }}
    a {{ color: var(--accent); }}
    ul {{ padding-left: 1.25rem; }}
    li {{ margin: 4px 0; }}
    code {{
      background: var(--card);
      border: 1px solid var(--border);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 0.9em;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px 20px;
      margin: 16px 0;
    }}
    footer {{
      margin-top: 48px;
      padding-top: 16px;
      border-top: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Privacy Policy</h1>
    <p class="meta">Live in a Week (Chrome Extension) &middot; Last updated: {LAST_UPDATED}</p>

    <p>
      Live in a Week is a new-tab weekly planner. This policy explains exactly what
      data we collect, why we collect it, where it is stored, and how you can have it deleted.
      We do not sell user data. We do not run analytics or advertising trackers.
    </p>

    <h2>1. What we collect</h2>
    <div class="card">
      <strong>Account information</strong>
      <ul>
        <li>Phone number — used as your unique login identifier.</li>
        <li>One-time password (OTP) — verified at sign-in, then discarded.</li>
        <li>Display name and profile picture URL — optional, shown in the app.</li>
        <li>Bearer access token — issued after successful OTP verification, stored locally in your browser via <code>chrome.storage.local</code> and sent to our server on each request to authenticate you.</li>
      </ul>
    </div>
    <div class="card">
      <strong>Task content you create</strong>
      <ul>
        <li>Task title, description, due date and time, energy level, priority, color, reminders, recurrence rules.</li>
        <li>Sync metadata (timestamps, version numbers) used to reconcile changes between your devices.</li>
      </ul>
    </div>
    <p>
      We do <em>not</em> collect: location, browsing history, the content of other websites you visit,
      health data, financial data, or contacts. We do not embed third-party analytics or advertising SDKs.
    </p>

    <h2>2. Why we collect it</h2>
    <ul>
      <li><strong>Authentication</strong> — verify it's you and keep you signed in.</li>
      <li><strong>Sync</strong> — make your tasks available across browsers and devices you sign in on.</li>
      <li><strong>Reminders</strong> — send the task reminders you have explicitly scheduled.</li>
    </ul>

    <h2>3. Where it is stored</h2>
    <ul>
      <li><strong>On your device</strong> — your tasks and the access token are kept in <code>chrome.storage.local</code>, so the planner works offline.</li>
      <li><strong>On our server</strong> — your profile and tasks are stored in our database for sync. Traffic is sent over HTTPS.</li>
    </ul>

    <h2>4. Third parties</h2>
    <p>
      We do not sell or rent your data. We share data only with the service providers strictly required to run the product:
    </p>
    <ul>
      <li><strong>WhatsApp Business / Meta Cloud API</strong> — used to deliver your OTP code and, if you opt in, reminder messages. Meta processes your phone number under its own privacy policy.</li>
      <li><strong>Our hosting and database provider</strong> — stores the data described above on our behalf.</li>
    </ul>

    <h2>5. Retention</h2>
    <p>
      Your account and tasks are kept for as long as your account exists. You can request deletion at
      any time (see below); on deletion, your profile and tasks are removed from our database. Backups
      that include deleted data roll off within 30 days.
    </p>

    <h2>6. Your rights</h2>
    <ul>
      <li><strong>Access / export</strong> — request a copy of your data.</li>
      <li><strong>Correction</strong> — update your display name from within the extension.</li>
      <li><strong>Deletion</strong> — request deletion of your account and all associated tasks.</li>
    </ul>
    <p>
      To exercise any of these rights, email <a href="mailto:kaushal.joshi@truboardpartners.com">kaushal.joshi@truboardpartners.com</a>
      from the phone number associated with your account or include it in the message body.
    </p>

    <h2>7. Children</h2>
    <p>Live in a Week is not directed to children under 13, and we do not knowingly collect their data.</p>

    <h2>8. Security</h2>
    <p>
      Data in transit is encrypted with HTTPS. Access tokens are scoped to your account and can be
      invalidated by signing out. We follow standard practices for credential storage, but no system is
      perfectly secure — please report suspected vulnerabilities to the contact email above.
    </p>

    <h2>9. Changes to this policy</h2>
    <p>
      If we materially change what we collect or how we use it, we will update the "Last updated"
      date at the top of this page. Continued use of the extension after a change constitutes
      acceptance of the revised policy.
    </p>

    <h2>10. Contact</h2>
    <p>
      Questions or data requests:
      <a href="mailto:kaushal.joshi@truboardpartners.com">kaushal.joshi@truboardpartners.com</a>
    </p>

    <footer>
      &copy; {date.today().year} Live in a Week. This policy applies only to the Live in a Week Chrome extension and its backend.
    </footer>
  </main>
</body>
</html>
"""


@router.get("/privacy", response_class=HTMLResponse, include_in_schema=False)
async def privacy_policy() -> HTMLResponse:
    return HTMLResponse(content=PRIVACY_HTML)
