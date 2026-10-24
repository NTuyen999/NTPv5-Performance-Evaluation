import csv
import re
from pathlib import Path

BASE = Path.home() / "ntpv5-project"
RESULTS = BASE / "results"

RUNS = [
    ("M1", "NTPv4", "Basic", "ntpv4_basic_local.log"),
    ("M2", "NTPv4", "Interleaved", "ntpv4_interleaved_local.log"),
    ("M3", "NTPv5", "Basic", "ntpv5_basic_local.log"),
    ("M4", "NTPv5", "Interleaved", "ntpv5_interleaved_local.log"),
]

NUM = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?"

PATTERN = re.compile(
    rf"(?P<mode>Basic|Interleaved) mode "
    rf"offset=(?P<offset>{NUM}) "
    rf"delay=(?P<delay>{NUM})"
    rf"(?:\s+rdist=(?P<rdist>{NUM}))?"
    rf"(?:\s+stratum=(?P<stratum>\d+))?"
)

samples = []
metadata = []

for mode_id, protocol, requested_mode, filename in RUNS:
    path = RESULTS / filename

    if not path.exists():
        print(f"ERROR: Missing {filename}")
        continue

    requests = 0
    responses = 0
    valid = 0
    matched = 0
    interleaved = 0

    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            if "Sent NTPv" in line and "request" in line:
                requests += 1

            if "Received NTPv" in line and "response" in line:
                responses += 1

            match = PATTERN.search(line)
            if not match:
                continue

            valid += 1
            actual_mode = match.group("mode")

            if actual_mode == requested_mode:
                matched += 1

            if actual_mode == "Interleaved":
                interleaved += 1

            offset = float(match.group("offset"))
            delay = float(match.group("delay"))

            samples.append({
                "run_id": f"LOCAL_{mode_id}",
                "scenario": "LOCAL",
                "rep": 0,
                "mode_id": mode_id,
                "protocol_requested": protocol,
                "mode_requested": requested_mode,
                "mode_actual": actual_mode,
                "sample_no": valid,
                "elapsed_s": "",
                "in_warmup": "unknown",
                "offset_s": offset,
                "delay_s": delay,
                "offset_ms": offset * 1000,
                "delay_ms": delay * 1000,
                "rdist_s": match.group("rdist") or "",
                "stratum": match.group("stratum") or "",
            })

    metadata.append({
        "run_id": f"LOCAL_{mode_id}",
        "scenario": "LOCAL",
        "rep": 0,
        "mode_id": mode_id,
        "protocol_requested": protocol,
        "mode_requested": requested_mode,
        "source_file": filename,
        "requests_sent": requests,
        "responses_received": responses,
        "valid_samples": valid,
        "matched_samples": matched,
        "interleaved_samples": interleaved,
        "valid_ratio": round(valid / requests, 6) if requests else "",
        "interleaved_ratio": (
            round(interleaved / valid, 6)
            if valid and requested_mode == "Interleaved"
            else ""
        ),
        "warmup_applied": False,
    })

    print(
        f"{mode_id}: sent={requests}, received={responses}, "
        f"valid={valid}, matched={matched}, interleaved={interleaved}"
    )


def save_csv(filename, rows):
    if not rows:
        return

    output = RESULTS / filename

    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print("Saved:", output)


save_csv("ntp_run_samples_local.csv", samples)
save_csv("ntp_run_metadata_local.csv", metadata)

print("Total valid samples:", len(samples))
print("Total runs:", len(metadata))
