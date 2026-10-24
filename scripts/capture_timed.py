import argparse
import subprocess
import sys
import time
from pathlib import Path

BASE = Path.home() / "ntpv5-project"
REPO = BASE / "ntp5-exp"
RESULTS = BASE / "results"

MODES = {
    "M1": ["-v", "4"],
    "M2": ["-v", "4", "-x"],
    "M3": ["-v", "5"],
    "M4": ["-v", "5", "-x"],
}

parser = argparse.ArgumentParser()
parser.add_argument("--mode", choices=MODES, required=True)
parser.add_argument("--warmup", type=float, default=60)
parser.add_argument("--name", default="pilot")
args = parser.parse_args()

RESULTS.mkdir(parents=True, exist_ok=True)
output = RESULTS / f"{args.name}_{args.mode}_timed.log"

cmd = [
    sys.executable,
    "-u",
    "ntpnode.py",
    "-p", "10124",
    "-i", "1",
    *MODES[args.mode],
    "127.0.0.1:10123",
]

print("Mode:", args.mode)
print("Warm-up:", args.warmup, "seconds")
print("Output:", output)

start = time.monotonic()

with output.open("w", encoding="utf-8") as log:
    process = subprocess.Popen(
        cmd,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        start_new_session=True,
    )

    try:
        for line in process.stdout:
            elapsed = time.monotonic() - start
            phase = (
                "WARMUP"
                if elapsed < args.warmup
                else "MEASURE"
            )

            record = (
                f"[{elapsed:.6f}] "
                f"[{phase}] "
                f"{line.rstrip()}"
            )

            print(record, flush=True)
            log.write(record + "\n")
            log.flush()

    except KeyboardInterrupt:
        print("\nStopping client...")

    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()

print("Saved:", output)
