# Load testing (M11 Phase G — dev-only)

`locustfile.py` models the reader/operator mix defined in the UI/UX design
system and API contracts.

## Run

```bash
pip install locust
locust -f tools/loadtest/locustfile.py --host https://staging.atozproducthub.dev
```

Open the Locust UI (`http://localhost:8089`), set users/spawn rate, and
track the SLO dashboard while it runs.

## Gates

- p95 latency < 500 ms and error rate < 1% at the target concurrency.
- No load against Pinterest/affiliate/AI OS external endpoints — publish
  and webhook paths are covered by the queue reliability tests instead.
- Run against staging, never production.
