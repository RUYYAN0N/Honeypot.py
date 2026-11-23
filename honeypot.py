import json
import os
import httpx
from datetime import datetime, timezone
from urllib import request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
IP_CACHE: dict[str, dict] = {}
LOG_FILE = ...

LOG_FILE = os.getenv("LOG_FILE", "./telemetry_data/telemetry.jsonl")
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

def emit_telemetry(event: dict):
    """Appends a single attack event as one JSON line."""
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")




import hashlib
import time
import uuid
from fastapi import FastAPI, Request, Response


app= FastAPI(docs_url=None, redoc_url=None, openapi_url=None)

@app.middleware("http")
async def capture_all_traffic(request: Request, call_next):
    start_time = time.time()

    #Read the request body
    raw_body = await request.body()
    body_text = raw_body.decode("utf-8", errors="replace")

    #extract the hacker's IP address
    client_ip = request.headers.get(
        "x-forwarded-for",
        request.client.host if request.client else "unknown"
    )

    #auto-tag the attack category based on the URL path and payload contents
    path = request.url.path.lower()
    tags = []
    if ".env" in path or "config" in path or ".git" in path:
        tags.append("sensitive_discovery")
    if "admin" in path or "login" in path:
        tags.append("credential_attack")
    if "/v1/" in path or "completions" in path:
        tags.append("ai_endpoint_abuse")
    if any(k in body_text.lower() for k in ["unicorn select", "../", "${jndi:", "wget ", "curl ", "/bin/sh"]):
        tags.append("exploit_payload")

    #forward the request to our decoy routes
    response: Response = await call_next(request)

    #build the strucured telemetry dictionary
    telemetry_record = {
        "event_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sensor": "corp-ai-gateway-01",
        "src_ip": client_ip,
        "src_port": request.client.port if request.client else None,
        "method": request.method,
        "path": request.url.path,
        "query_params": dict(request.query_params),
        "headers": dict(request.headers),
        "user_agent": request.headers.get("user-agent", ""),
        "body_preview": body_text[:4096], #limit to 4kd so large payloads dont overwhelm the log
        "body_sha256": hashlib.sha256(raw_body).hexdigest() if raw_body else None,
        "status_code": response.status_code,
        "tags": tags or ["recon_scan"],
        "latency_ms": round((time.time() - start_time) * 1000, 2),
    }

    #write the record to the telemetry log file (jsonl)
    emit_telemetry(telemetry_record)

    #spoof realistic server headers to make it look like a nginx reverse proxy in front of a real AI endpoint
    response.headers["Server"] = "nginx/1.24.0 (Ubuntu)"
    response.headers["X-Powered-By"] = "CorpAI-Router/2.4.1"
    return response






@app.get("/", response_class=HTMLResponse)
async def root():
    """Realistic fake internal AI portal with the interactive bait buttons."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>CorpAI Internal LLM Gateway v2.4.1</title>
        <style>
            body{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 40px; }
            .container { max-width: 760px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 30px; }
            .badge { background: #f59e0b; color: #0f172a; font-weight: bold; padding: 4px 10px; border-radius: 4px; font-size: 12px; }
            h1 { margin-top: 12px; font-size: 24px; color: #f8fafc; }
            p { color: #94a3b8; line-height: 1.6; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
            .card { background: #0f172a; border: 1px solid #334155; padding: 18px; border-radius: 8px; }
            .card h3 { margin: 0 0 8px 0; font-size: 16px; color: #38bdf8; }
            button, a.btn { display: inline-block; margin-top: 10px; background: #2563eb; color: white; border: none; padding: 8px 14px; border-radius: 6px; text-decoration: none; font-size: 14px; cursor: pointer; }
            button:hover, a.btn:hover { background: #1d4ed8; }
            .danger { background: #dc2626; }
            .danger:hover { background: #b91c1c; }
            input { width: 92%; padding: 8px; margin: 6px 0; background: #1e293b; border: 1px solid #475569; color: white; border-radius: 4px; }
            pre { background: #020617; padding: 12px; border-radius: 6px; overflow-x: auto; font-size: 13px; color: #34d399; display: none; }
        </style>
    </head>
    <body>
        <div class="container">
            <span class="badge">STATUS: DEGRADED (DEBUG MODE ENABLED)</span>
            <h1>CorpAI Internal LLM Inference Gateway</h1>
            <p>Internal model router for <strong>gpt-4o-internal</strong> and <strong>claude-enterprise</strong>. Unauthorized external access is prohibited.</p>

            <div class="grid">
                <div class="card">
                    <h3>1. Operator Authentication</h3>
                    <input id="user" placeholder="Username (e.g. sysadmin)" />
                    <input id="pass" type="password" placeholder="Password" />
                    <button onclick="tryLogin()">Sign In to Console</button>
                </div>

                <div class="card">
                    <h3>2. Legacy Config & Diagnostics</h3>
                    <p style="font-size:13px;">Temporary maintenance links left exposed during v2.4.1 migration:</p>
                    <a class="btn danger" href="/.env">View Backup .env</a>
                    <button onclick="runDiag()">Run Node Health Check</button>
                </div>
            </div>

            <pre id="output"></pre>
            <p style="margin-top: 24px; font-size: 12px; border-top: 1px solid #334155; padding-top: 14px;">
                Security Researcher / Hack Club Reviewer? <a href="/dashboard" style="color:#38bdf8;">View Live Attack Telemetry Dashboard &rarr;</a>
            </p>
        </div>

        <script>
            async function tryLogin() {
                const res = await fetch('/admin/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({
                        username: document.getElementById('user').value,
                        password: document.getElementById('pass').value
                    })
                });
                const out = document.getElementById('output');
                out.style.display = 'block';
                out.textContent = JSON.stringify(await res.json(), null, 2);
            }

            async function runDiag() {
                const res = await fetch('/admin/exec-diag', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({command: 'uname -a'})
                });
                const out = document.getElementById('output');
                out.style.display = 'block';
                out.textContent = JSON.stringify(await res.json(), null, 2);
            }
        </script>
    </body>
    </html>"""





@app.get("/.env")
async def fake_env():
    """Honeytoken trap: lures attackers into usingfake credentials on /admin/login"""
    fake_secrets = (
        "APP_ENV=production/n"
        "ADMIN_USER=sysadmin/n"
        "ADMIN_PASS=CorpAI_2026!Prod\n"
        "OPENAI_API_KEY=sk-proj-a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4\n"
        "DB_URL=postgres://corpai:Pr0dDP@aa!@10.0.4.12:5432/gateway\n"
    )
    return PlainTextResponse(fake_secrets, status_code=200)



@app.post("/admin/login")
async def fake_login(request: Request):
    """Grants a fake session token if the attackerthe .env honeytoke or weak passwords."""
    try:
        data = await request.json()
    except Exception:
        data = {}

    username = data.get("username", "")
    password = data.get("password", "")

    if (username == "sysadmin" and password == "CorpAI_2026!Prod") or password in ["admin", "123456", "password"]:
        return JSONResponse(
            status_code=200,
            content={
                "status": "authenticated",
                "role": "superadmin",
                "session_token": f"sess_{uuid.uuid4().hex}",
                "endpoints": ["/admin?exec-diag", "/v1/chat/completions"],
            },
        )
    return JSONResponse(status_code=401, content={"error": "invalid credentials"})

@app.post("/admin/exec-diag")
async def fake_rce_diagnostics(request: Request):
    """Captures post-exploitation commands by returning realistic fake Linux output."""
    try:
        data = await request.json()
    except Exception:
        data = {}


    cmd = data.get("command", "uptime")
    fake_outputs = {
        "id": "uid=0(root) gid=0(root) groups=0(root)",
    "whoami": "root",
    "uname -a": "Linux corp-ai-gw-01 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux",
    }
    output = fake_outputs.get(cmd.strip(), f"sh: 1: {cmd.split()[0] if cmd else 'cmd'}: completed with exit code 0")
    return {"host": "corp-ai-gw-01", "stdout": output, "stderr": ""}

@app.get("/dashboard", response_class=HTMLResponse)
async def live_telemetry_dashboard():
    """Visual HTML dashboard displaying live captured attack telemetry."""
    events = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

    rows = ""
    for e in reversed(events[-25:]):
        intel = e.get("threat_intel", {})
        loc = f"{intel.get('country', 'Unknown')} ({intel.get('isp', 'Unknown')})"
        tags = ", ".join(e.get("tags", []))
        rows += f"""
        <tr>
            <td>{e['timestamp'][:19]}Z</td>
            <td><code>{e['src_ip']}</code></td>
            <td>{loc}</td>
            <td><strong>{e['method']}</strong> {e['path']}</td>
            <td><span class="tag">{tags}</span></td>
        </tr>
        """

    if not rows:
        rows = "<tr><td colspan='5' style='text-align:center;color:#94a3b8;'>No attacks logged yet-visit / and click a bait button to test!</td></tr>"

    return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Honeypot Live Attack Telemetry</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #090d16; color: #e2e8f0; padding: 30px; }}
                .wrap {{ max-width: 1000px; margin: 0 auto; }}
                h1 {{ color: #38bdf8; margin-bottom: 6px; }}
                .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                .stat-box {{ background: #1e293b; padding: 16px 24px; border-radius: 8px; border: 1px solid #334155; }}
                table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
                th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid #334155; font-size: 13px; }}
                th {{ background: #0f172a; color: #94a3b8; text-transform: uppercase; font-size: 11px; }}
                .tag {{ background: #7f1d1d; color: #fca5a5; padding: 3px 8px; border-radius: 4px; font-size: 11px; }}
                a {{ color: #38bdf8; }}
            </style>
        </head>
        <body>
            <div class="wrap">
                <h1>Live Attack Telemetry Dashboard</h1>
                <p>Real-time intrusion feed captured by the <strong>CorpAI Medium-Interaction Honeypot</strong>. <a href="/">&larr; Back to Decoy Gateway</a></p>
                <div class="stats">
                    <div class="stat-box"><strong>Total Events Captured:</strong> {len(events)}</div>
                    <div class="stat-box"><strong>Active Decoys:</strong> <code>/.env</code>, <code>/admin/login</code>, <code>/admin/exec-diag</code></div>
                </div>
                <table>
                    <thead>
                        <tr><th>Timestamp (UTC)</th><th>Source IP</th><th>GeoIP / ISP</th><th>Request</th><th>Threat Tags</th></tr>
                    </thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </body>
        </html>
        """


@app.api_route("/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def catch_all(full_path: str):
    """Catches all other random scanner paths."""
    return JSONResponse(status_code=404, content={"error": "Endpoint not found", "path": f"/{full_path}"})



async def enrich_ip(ip: str) -> dict:
    """Looks up country, ISP, and hosting/proxy status for public IPs."""
    # Skip lookup for local/private test IPs.
    if ip in ("127.0.0.1", "::1", "localhost", "unknown") or ip.startswith(("10.", "192.168", "172.")):
        return {"country": "Local/Private", "isp": "Loopback", "is_hosting": False, "is_proxy": False}

    if ip in IP_CACHE:
        return IP_CACHE[ip]

    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(
                f"http://ip-api.com/json/{ip}",
                params={"fields": "status,country,city,isp,org,hosting,proxy"},
            )
            data = response.json()
            if data.get("status") == "success":
                intel = {
                    "country": data.get("country", "Unknown"),
                    "city": data.get("city", "Unknown"),
                    "isp": data.get("isp", "Unknown"),
                    "is_hosting": data.get("hosting", False),
                    "is_proxy": data.get("proxy", False),
                }
                IP_CACHE[ip] = intel
                return intel
    except Exception:
        pass

    return {
        "country": "Lookup Failed",
        "city": "Unknown",
        "isp": "Unknown",
        "is_hosting": False,
        "is_proxy": False,
    }