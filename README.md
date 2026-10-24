# NTPv5 Performance Evaluation

## Project
Performance Evaluation of NTPv4 and NTPv5 under Unstable Network Conditions.

## Team
- P1 - Tuyen: Protocol analysis, data processing, KPI and visualization.
- P2 - Tung: Network topology, NetEm configuration and experiment runner.

## Evaluation Modes
- M1: NTPv4 Basic
- M2: NTPv4 Interleaved
- M3: NTPv5 Basic
- M4: NTPv5 Interleaved

## Network Scenarios
- S0: Baseline
- S1: Symmetric delay 25/25 ms
- S2: Delay 25 +/- 10 ms in both directions
- S3: S2 with 5% packet loss in both directions
- S4: Asymmetric delay 10/40 ms

## Tools
- Ubuntu Linux
- Python 3
- Linux Network Namespace
- tc NetEm
- ntp5-exp

Upstream: https://github.com/mlichvar/ntp5-exp

Tested upstream commit:
fe19210790b2a1cbd951e3e5066dca094dd62a52

## Current Status
- M1-M4 localhost smoke tests completed.
- Log parsing and CSV export completed.
- Timed logging and warm-up separation tested.
- Main NetEm experiments and statistical analysis pending.

## Important
The current scripts are prototypes tested on P1's local environment.
Paths and addresses must be configurable before team integration.

Do not use localhost results as official performance conclusions.
