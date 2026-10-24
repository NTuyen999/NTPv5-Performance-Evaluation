import argparse
import csv
import re
from pathlib import Path

MODES = {
    "M1": ("NTPv4", "Basic"),
    "M2": ("NTPv4", "Interleaved"),
    "M3": ("NTPv5", "Basic"),
    "M4": ("NTPv5", "Interleaved"),
}

parser = argparse.ArgumentParser()
parser.add_argument("--log", required=True)
parser.add_argument("--mode", choices=MODES, required=True)
parser.add_argument("--scenario", default="LOCAL")
parser.add_argument("--rep", type=int, default=0)
args = parser.parse_args()

source = Path(args.log).expanduser().resolve()

if not source.is_file():
    parser.error(f"Khong tim thay log: {source}")

output_dir = Path.home() / "ntpv5-project/results/parsed"
output_dir.mkdir(parents=True, exist_ok=True)

run_id = source.stem
protocol, requested_mode = MODES[args.mode]

number = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

time_pattern = re.compile(
    r"^\[(\d+(?:\.\d+)?)\]\s+"
    r"\[(WARMUP|MEASURE)\]\s+(.*)$"
)

sample_pattern = re.compile(
    rf"(Basic|Interleaved) mode\s+"
    rf"offset=({number})\s+delay=({number})"
    rf"(?:\s+rdist=({number}))?"
    rf"(?:\s+stratum=(\d+))?"
)

counts = {
    "WARMUP": {"sent": 0, "received": 0, "valid": 0, "interleaved": 0},
    "MEASURE": {"sent": 0, "received": 0, "valid": 0, "interleaved": 0},
}

rows = []
sample_no = 0
last_protocol = ""

with source.open(encoding="utf-8", errors="replace") as file:
    for line in file:
        timed = time_pattern.match(line.strip())

        if not timed:
            continue

        elapsed = float(timed.group(1))
        phase = timed.group(2)
        message = timed.group(3)

        c = counts[phase]

        if "Sent NTPv" in message and "request" in message:
            c["sent"] += 1

        if "Received NTPv" in message and "response" in message:
            c["received"] += 1
            version = re.search(r"Received NTPv([45]) response", message)
            if version:
                last_protocol = "NTPv" + version.group(1)

        match = sample_pattern.search(message)

        if not match:
            continue

        sample_no += 1
        c["valid"] += 1

        actual_mode = match.group(1)
        offset = float(match.group(2))
        delay = float(match.group(3))

        if actual_mode == "Interleaved":
            c["interleaved"] += 1

        rows.append({
            "run_id": run_id,
            "scenario": args.scenario,
            "rep": args.rep,
            "mode_id": args.mode,
            "protocol_requested": protocol,
            "protocol_actual": last_protocol,
            "mode_requested": requested_mode,
            "mode_actual": actual_mode,
            "sample_no": sample_no,
            "elapsed_s": elapsed,
            "in_warmup": phase == "WARMUP",
            "offset_s": offset,
            "delay_s": delay,
            "offset_ms": offset * 1000,
            "delay_ms": delay * 1000,
            "rdist_s": match.group(4) or "",
            "stratum": match.group(5) or "",
        })

samples_file = output_dir / f"{run_id}_samples.csv"

if rows:
    with samples_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

metadata = {
    "run_id": run_id,
    "scenario": args.scenario,
    "rep": args.rep,
    "mode_id": args.mode,
    "protocol_requested": protocol,
    "mode_requested": requested_mode,
    "warmup_requests": counts["WARMUP"]["sent"],
    "warmup_valid": counts["WARMUP"]["valid"],
    "measure_requests": counts["MEASURE"]["sent"],
    "measure_responses": counts["MEASURE"]["received"],
    "measure_valid": counts["MEASURE"]["valid"],
    "measure_interleaved": counts["MEASURE"]["interleaved"],
}

metadata["valid_ratio"] = (
    counts["MEASURE"]["valid"] / counts["MEASURE"]["sent"]
    if counts["MEASURE"]["sent"] else ""
)

metadata["interleaved_ratio"] = (
    counts["MEASURE"]["interleaved"] / counts["MEASURE"]["valid"]
    if counts["MEASURE"]["valid"] and requested_mode == "Interleaved"
    else ""
)

metadata_file = output_dir / f"{run_id}_metadata.csv"

with metadata_file.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(metadata.keys()))
    writer.writeheader()
    writer.writerow(metadata)

print("========== NTP TIMED PARSER ==========")
print("Run:", run_id)
print("Mode:", args.mode)
print("Warm-up:", counts["WARMUP"])
print("Measure:", counts["MEASURE"])
print("Total samples:", len(rows))
print("Saved samples:", samples_file)
print("Saved metadata:", metadata_file)
