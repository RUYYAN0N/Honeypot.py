import json
import os
import httpx
from collections import Counter

LOG_FILE = os.getenv("LOG_FILE", "./telemtry_data/telemetry.jsonl")


def load_events(filepath: str) -> list[dict]:
    """Reads a JSONL telemetry file and returns a list of event dictionaries."""
    if not os.path.exists(filepath):
        print(f"[!] No telemetry file found at {filepath}")
        return []

    events = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"[!] Skipping corrupted JSON on line {line_num}")
    return events



def generate_report(events: list[dict]):
    if not events:
        print("No events to analyze yet.")
        return

    ip_counts = Counter()
    path_counts = Counter()
    tag_counts = Counter()
    captured_payloads = []

    for ev in events:
        ip_counts[ev.get("src_ip", "unknown")] += 1
        path_counts[f"{ev.get('method')} {ev.get('path')}"] += 1

        for tag in ev.get("tags", []):
            tag_counts[tag] += 1


        #extract any non empty request bodies (credentials or commands
        body = ev.get("body_preview", "").strip()
        if body:
            captured_payloads.append({
                "timestamp": ev.get("timestamp"),
                "src_ip": ev.get("src_ip"),
                "path": ev.get("path"),
                "payload": body,
                "sha256": ev.get("body_sha256"),
            })



    # Print the report
    print("\n" + "=" * 55)
    print("TELEMETRY ANALYSIS REPORT")
    print("=" * 55)
    print(f"Total Events Captured : {len(events)}")
    print(f"Unique Source IPs     : {len(ip_counts)}")

    print("\n--- Attack Categories (Tags) ---")
    for tag, count in tag_counts.most_common():
        print(f" {tag:<22} : {count}")

    print("\n--- Top Attack IPs ---")
    for ip, count in ip_counts.most_common(5):
        print(f" {ip:<22} : {count}")

    print("\n--- Captured Exploit / Credential Payloads ---")
    if not captured_payloads:
        print(" None captured yet.")
    else:
        for item in captured_payloads:
            print(f"  [{item['timestamp']}] {item['src_ip']} -> {item['path']}")
            print(f"   Payload : {item['payload']}")
            print(f"   SHA-256 : {item['sha256']}\n")


if __name__ == "__main__":
    telemetry_events = load_events(LOG_FILE)
    generate_report(telemetry_events)



#cache IP lookups in memory so repeat scans dont hit API rate limits
IP_CACHE: dict[str, dict] = {}

