import csv
import re
from pathlib import Path

# Thu muc du an
BASE = Path.home() / "ntpv5-project"
RESULTS = BASE / "results"

# Danh sach file log
LOG_FILES = [
    ("ntpv4_basic_local.log", "NTPv4", "Basic"),
    ("ntpv4_interleaved_local.log", "NTPv4", "Interleaved"),
    ("ntpv5_basic_local.log", "NTPv5", "Basic"),
    ("ntpv5_interleaved_local.log", "NTPv5", "Interleaved"),
]

# Tim offset va delay trong log
NUMBER = r"([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)"

PATTERN = re.compile(
    rf"(Basic|Interleaved) mode\s+"
    rf"offset={NUMBER}\s+delay={NUMBER}"
)

all_rows = []

for filename, protocol, requested_mode in LOG_FILES:

    filepath = RESULTS / filename

    if not filepath.exists():
        print(f"Khong tim thay: {filename}")
        continue

    count = 0

    with open(filepath, "r", encoding="utf-8", errors="replace") as f:

        for line in f:

            match = PATTERN.search(line)

            if not match:
                continue

            actual_mode = match.group(1)
            offset = float(match.group(2))
            delay = float(match.group(3))

            count += 1

            all_rows.append({
                "source_file": filename,
                "protocol": protocol,
                "requested_mode": requested_mode,
                "actual_mode": actual_mode,
                "sample_no": count,
                "offset_s": offset,
                "delay_s": delay,
                "offset_ms": offset * 1000,
                "delay_ms": delay * 1000,
            })

    print(f"{filename}: {count} samples")

# Luu CSV
if all_rows:

    output = RESULTS / "ntp_local_samples.csv"

    with open(output, "w", newline="", encoding="utf-8") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=list(all_rows[0].keys())
        )

        writer.writeheader()
        writer.writerows(all_rows)

    print("---------------------------")
    print(f"Tong so mau: {len(all_rows)}")
    print(f"Da luu CSV: {output}")

else:
    print("Khong tim thay mau NTP hop le!")
