# Honeypot.py
# CorpAI Medium-Interaction Honeypot & Attack Telemetry

A custom, medium-interaction cybersecurity honeypot built in Python with **FastAPI**. Instead of immediately rejecting scanners with generic `404` errors, this project mimics a misconfigured internal **LLM Inference Gateway** with an interactive web portal, leaked honeytokens, and stateful post-exploitation traps to capture multi-stage attacker behavior.

- **Live Demo & Decoy Portal:** [https://onrender.comdashboard](https://ai-honeypot-telemetry.onrender.com/)
- **Live Attack Telemetry Dashboard:** [https://onrender.comdashboard](https://ai-honeypot-telemetry.onrender.com/)

---

## How It Works

1. **Interactive Bait Portal (`/`):** Presents a convincing internal AI gateway interface with debug mode enabled, tempting automated bots and human attackers to probe exposed buttons and login forms.
2. **HTTP Interception Middleware:** Every incoming request passes through a FastAPI middleware layer before reaching any route—capturing source IPs, headers, user agents, SHA-256 payload hashes, and auto-tagging attack categories (`secret_discovery`, `credential_attack`, `ai_endpoint_abuse`, `exploit_payload`).
3. Stateful Decoy Traps:
   - `GET /.env` — Serves realistic fake production credentials and API keys (honeytokens).
   - `POST /admin/login` — Accepts the leaked `.env` credentials (or common weak passwords) and grants a fake `superadmin` session token.
   - `POST /admin/exec-diag` — Simulates a vulnerable command-execution diagnostic endpoint, returning realistic Linux output (`uid=0(root)`) so attackers reveal their second-stage commands.
4. **Real-Time Threat-Intel Enrichment:** Uses asynchronous `httpx` requests (with in-memory caching) to enrich attacking IPs with country, city, ISP, and hosting/proxy metadata.
5. **Telemetry Analyzer (`analyze.py`):** A companion CLI tool that parses `telemetry.jsonl` to summarize top attacking IPs, targeted endpoints, and captured payloads.

---

## Running Locally

```bash
git clone https://github.com
cd Honeypot.py
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn honeypot:app --host 127.0.0.1 --port 8080 --reload
```

To generate a CLI threat summary from captured logs:
```bash
python analyze.py
```

---

## Dev Log

- **Day 1 — Architecture & JSONL Telemetry Engine:** Decided on a medium-interaction HTTP decoy mimicking an internal AI gateway rather than a low-interaction port listener. Built a structured JSONL logger so high-frequency scanner traffic can be parsed line-by-line without memory bloat.
- **Day 2 — Middleware Wiretap & Stateful Decoys:** Implemented FastAPI HTTP middleware to intercept all traffic (including `404` probes), compute SHA-256 hashes of incoming payloads, and tag attack patterns. Built the `/.env` -> `/admin/login` -> `/admin/exec-diag` breadcrumb trail and verified the 3-stage exploit chain locally.
- **Day 3 — Threat-Intel Enrichment, Web UI & Cloud Deployment:** Added async GeoIP/ISP lookup with caching (`httpx`), built `analyze.py` for offline log triage, upgraded `/` and `/dashboard` into a full interactive web portal + SOC telemetry view, and deployed to Render.

# CorpAI Medium-Interaction Honeypot & Covert Attack Telemetry

A custom, medium-interaction cybersecurity honeypot built in Python with **FastAPI**. Instead of tipping off attackers with an obvious telemetry page or immediately rejecting scanners with `404` responses, this application mimics a misconfigured internal **LLM Inference Gateway** with interactive bait controls and a **covert operator command** (`telemetry --show`) that unlocks live intrusion telemetry directly inside the decoy console.

- **Live Demo & Decoy Portal:** https://ai-honeypot-telemetry.onrender.com/

---

## How to Test the Demo (For Hack Club Reviewers)

1. **Act as an Attacker:** Open the [Live Demo](https://ai-honeypot-telemetry.onrender.com/), click **View Backup .env** to steal the fake credentials (`sysadmin` / `CorpAI_2026!Prod`), sign into the **Operator Authentication** box, or run fake shell commands like `whoami` in the **Diagnostics** box. Every action is silently logged with GeoIP and payload hashes.
2. **Unlock Live Telemetry (Covert Operator Mode):** In the **Legacy Config & Diagnostics** input box on the homepage, type the secret command:
   ```text
   telemetry --show
