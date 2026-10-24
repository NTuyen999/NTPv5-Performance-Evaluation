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
    parser.error(f"Log not found: {source}")

output_dir = source.parent / "parsed"
output_dir.mkdir(parents=True, exist_ok=True)

run_id = source.stem
protocol, requested_mode = MODES[args.mode]

NUM = r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?"

TIMED = re.compile(
    r"^\[(\d+(?:\.\d+)?)\]\s+"
    r"\[(WARMUP|MEASURE)\]\s+(.*)$"
)

SAMPLE = re.compile(
    rf"(Basic|Interleaved) mode\s+"
    rf"offset=({NUM})\s+delay=({NUM})"
    rf"(?:\s+rdist=({NUM}))?"
    rf"(?:\s+stratum=(\d+))?"
)

COUNTS = {
    phase: {
        "sent": 0,
        "received": 0,
        "valid": 0,
        "interleaved": 0
    }
    for phase in ("WARMUP", "MEASURE")
}

rows = []
sample_no = 0
pending = None
ready = None
unmatched_responses = 0
orphan_samples = 0

with source.open(encoding="utf-8", errors="replace") as f:
    for line in f:
        event = TIMED.match(line.strip())
        if not event:
            continue

        elapsed = float(event.group(1))
        phase = event.group(2)
        message = event.group(3)

        if "Sent NTPv" in message and "request" in message:
            COUNTS[phase]["sent"] += 1
            pending = {
                "phase": phase,
                "elapsed": elapsed
            }
            ready = None
            continue

        if "Received NTPv" in message and "response" in message:
            if pending is None:
                unmatched_responses += 1
                ready = None
                continue

            version = re.search(
                r"Received NTPv([45]) response", message
            )

            ready = {
                "phase": pending["phase"],
                "protocol": (
                    "NTPv" + version.group(1)
                    if version else ""
                )
            }

            COUNTS[ready["phase"]]["received"] += 1
            pending = None
            continue

        match = SAMPLE.search(message)
        if not match:
            continue

        if ready is None:
            orphan_samples += 1
            continue

        # Attribute sample to the request's phase,
        # not the response arrival phase.
        assigned_phase = ready["phase"]
        c = COUNTS[assigned_phase]

        sample_no += 1
        c["valid"] += 1

        actual_mode = match.group(1)
        if actual_mode == "Interleaved":
            c["interleaved"] += 1

        offset = float(match.group(2))
        delay = float(match.group(3))

        rows.append({
            "run_id": run_id,
            "scenario": args.scenario,
            "rep": args.rep,
            "mode_id": args.mode,
            "protocol_requested": protocol,
            "protocol_actual": ready["protocol"],
            "mode_requested": requested_mode,
            "mode_actual": actual_mode,
            "sample_no": sample_no,
            "elapsed_s": elapsed,
            "in_warmup": assigned_phase == "WARMUP",
            "offset_s": offset,
            "delay_s": delay,
            "offset_ms": offset * 1000,
            "delay_ms": delay * 1000,
            "rdist_s": match.group(4) or "",
            "stratum": match.group(5) or "",
        })

        ready = None

metadata = {
    "run_id": run_id,
    "scenario": args.scenario,
    "rep": args.rep,
    "mode_id": args.mode,
    "protocol_requested": protocol,
    "mode_requested": requested_mode,
    "warmup_requests": COUNTS["WARMUP"]["sent"],
    "warmup_valid": COUNTS["WARMUP"]["valid"],
    "measure_requests": COUNTS["MEASURE"]["sent"],
    "measure_responses": COUNTS["MEASURE"]["received"],
    "measure_valid": COUNTS["MEASURE"]["valid"],
    "measure_interleaved": COUNTS["MEASURE"]["interleaved"],
}

measure = COUNTS["MEASURE"]

metadata["valid_ratio"] = (
    measure["valid"] / measure["sent"]
    if measure["sent"] else ""
)

metadata["interleaved_ratio"] = (
    measure["interleaved"] / measure["valid"]
    if measure["valid"] and requested_mode == "Interleaved"
    else ""
)

def save_csv(path, data):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=list(data[0].keys())
        )
        writer.writeheader()
        writer.writerows(data)

if rows:
    save_csv(
        output_dir / f"{run_id}_samples.csv",
        rows
    )

save_csv(
    output_dir / f"{run_id}_metadata.csv",
    [metadata]
)

print("===== PARSER V2 =====")
print("Warm-up:", COUNTS["WARMUP"])
print("Measure:", COUNTS["MEASURE"])
print("Unmatched responses:", unmatched_responses)
print("Orphan samples:", orphan_samples)
print("Valid ratio:", metadata["valid_ratio"])
print("Interleaved ratio:", metadata["interleaved_ratio"])
print("Saved to:", output_dir)
