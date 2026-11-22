import json
import os
import httpx
from datetime import datetime, timezone
from urllib import request
from fastapi.responses import JSONResponse, PlainTextResponse
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




@app.get("/")
async def root():
    return {
        "service": "CorpAI Internal LLM Gateway",
        "version": "2.4.1-prod",
        "status": "degraded",
        "docs": "/admin/login",
    }


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

@app.get("/dashboard")
async def live_telemetry_dashboard():
    """Public read-only summary endpoint so demo reviewers can see live attack stats."""
    events = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

    recent = [
        {
            "timestamp": e["timestamp"],
            "src_ip": e["src_ip"],
            "country": e.get("threat_intel", {}).get("country", "Unknown"),
            "isp": e.get("threat_intel", {}).get("isp", "Unknown"),
            "method": e["method"],
            "path": e["path"],
            "tags": e["tags"],
        }
        for e in events[-15:]
    ]

    return {
        "honeypot": "CorpAI Internal LLM Gateway",
        "total_attacks_captured": len(events),
        "try_decoy_endpoints": ["/.env", "/admin/login", "/admin/exec-diag"],
        "recent_telemetry": recent,
    }


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