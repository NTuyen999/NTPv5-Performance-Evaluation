import argparse
import csv
import math
import statistics
from pathlib import Path


def percentile(values, percentage):
    values = sorted(values)
    if not values:
        return float("nan")
    if len(values) == 1:
        return values[0]

    pos = (len(values) - 1) * percentage / 100
    low = math.floor(pos)
    high = math.ceil(pos)

    return values[low] + (
        values[high] - values[low]
    ) * (pos - low)


parser = argparse.ArgumentParser()
parser.add_argument("--samples", required=True)
parser.add_argument("--metadata", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()

with open(args.samples, newline="", encoding="utf-8") as f:
    samples = list(csv.DictReader(f))

with open(args.metadata, newline="", encoding="utf-8") as f:
    metadata = list(csv.DictReader(f))

if not samples or len(metadata) != 1:
    raise SystemExit("ERROR: Invalid samples or metadata")

meta = metadata[0]

# Only use measurements after warm-up
measured = [
    row for row in samples
    if row["in_warmup"].strip().lower() == "false"
]

# Keep actual mode separate from requested mode
matched = [
    row for row in measured
    if row["mode_actual"] == meta["mode_requested"]
    and row["protocol_actual"] == meta["protocol_requested"]
]

if not matched:
    raise SystemExit("ERROR: No matching measurement samples")

offsets = [float(r["offset_ms"]) for r in matched]
delays = [float(r["delay_ms"]) for r in matched]
absolute = [abs(value) for value in offsets]

result = {
    "run_id": meta["run_id"],
    "scenario": meta["scenario"],
    "rep": meta["rep"],
    "mode_id": meta["mode_id"],
    "measure_requests": meta["measure_requests"],
    "measure_responses": meta["measure_responses"],
    "measure_valid": len(measured),
    "matched_samples": len(matched),
    "interleaved_samples": sum(
        r["mode_actual"] == "Interleaved"
        for r in measured
    ),
    "bias_ms": statistics.mean(offsets),
    "mae_ms": statistics.mean(absolute),
    "p95_abs_offset_ms": percentile(absolute, 95),
    "std_offset_ms": (
        statistics.stdev(offsets)
        if len(offsets) > 1 else 0.0
    ),
    "mean_delay_ms": statistics.mean(delays),
    "p95_delay_ms": percentile(delays, 95),
    "valid_ratio": meta["valid_ratio"],
    "interleaved_ratio": meta["interleaved_ratio"],
}

output = Path(args.out)
output.parent.mkdir(parents=True, exist_ok=True)

with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=result.keys())
    writer.writeheader()
    writer.writerow(result)

print("\n===== NTP KPI ANALYSIS =====")
for key, value in result.items():
    if isinstance(value, float):
        print(f"{key}: {value:.6f}")
    else:
        print(f"{key}: {value}")

print("\nSaved:", output)
print("NOTE: Valid ratio is preliminary until")
print("request-response pairing is verified.")
