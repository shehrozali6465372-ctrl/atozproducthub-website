# Load testing (M11 Phase G / Phase F — dev/staging only)

`locustfile.py` models the reader/operator/probe mix defined in the UI/UX
design system and API contracts. `baselines.yml` is the frozen threshold
set for staging (Task 24 / M11 Phase 3, ADR-0014).

## Run

```bash
pip install locust
locust -f tools/loadtest/locustfile.py --host https://staging.atozproducthub.dev
```

Open the Locust UI (`http://localhost:8089`), set users/spawn rate, and
track the SLO dashboard while it runs.

Headless run with the baseline profile:

```bash
pip install locust
locust -f tools/loadtest/locustfile.py --host https://staging.atozproducthub.dev \
  --headless -u 50 -r 5 --run-time 5m --csv=staging-load
```

## Gates

- p95 latency < 500 ms and error rate < 1% at the target concurrency.
- Full threshold set: `tools/loadtest/baselines.yml` (p50/p95/p99, error
  rate, queue depth, worker processing time, DB connection pressure).
- Every scenario in `baselines.yml` is covered by a user class in
  `locustfile.py`; coverage is asserted in `tests/staging/`.
- No load against Pinterest/affiliate/AI OS external endpoints — publish
  and webhook paths are covered by the queue reliability tests instead.
- Run against staging, never production.
