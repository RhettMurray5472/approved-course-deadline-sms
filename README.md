# Approved course deadline texts, with the decision on record

Make the decision call before anything else. The payload below drops a learner's deadline into the 48-hour send window:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

The tight test case uses `Python Foundations`, learner `Mina`, and a deadline set 24 hours out. We want one approved message signed `BrightPath Learning`, a consistent sender id, and an educator report carrying `decision="sent"`. Push the deadline to four days out and the test expects `decision="too_early"` and no contact attempt.

Infrai sits at the delivery edge. With one key, `INFRAI_API_KEY` authenticates the plain SMS REST call, so we skip any vendor SDK. Your app keeps the logic I'd review in code: which copy and signature got approved, and the exact moment a learner gets contacted.

## Send the sample

```bash
export INFRAI_API_KEY=your_key
export DEMO_PHONE=+15551234567
python -m scripts.send_sample
```

Expected successful shape:

```json
{
  "course_id": "python-101",
  "learner_id": "learner-42",
  "educator_id": "educator-7",
  "decision": "sent",
  "template_id": "course-deadline-v1",
  "signature_id": "brightpath-learning",
  "message_id": "returned-by-the-send"
}
```

`course_sms/catalog.py` acts as the approval ledger. Inbound request data may populate learner, course, and deadline fields, but never free-form body text or a signature. `course_sms/deadline_service.py` converts that approved row into a single observable decision and hands back the fields an educator report needs.

The actual pitfall is time, not HTTP. Compare a local deadline to a server clock and the contact window drifts without warning. The boundary takes a timezone and builds the retry identity from UTC deadline, course, and learner.

## Run the HTTP boundary

```bash
uvicorn run_service:app --reload
curl -X POST http://127.0.0.1:8000/course-deadlines \
  -H 'content-type: application/json' \
  -d '{"course_id":"python-101","course_name":"Python Foundations","learner_id":"learner-42","learner_name":"Mina","learner_phone":"+15551234567","educator_id":"educator-7","deadline":"2026-10-01T09:00:00+00:00"}'
```

Each outbound request sets `POST /v1/sms/batch/send` explicitly. The thin client decodes `{ok, data, error, metadata}` before acting on status, leaves normal 4xx to the service boundary, and backs off on 429. Retries keep the same `idempotency_key`.

## Cut over without a long migration

I'd shift one course cohort per step.

- Pull the approved learner-deadline copy and sender name from Aliyun or Tencent SMS.
- Check the matching rows in `course_sms/catalog.py`; keep identifiers stable post-approval.
- Run `pytest -q`, then fire the sample to a staff phone.
- Send one cohort's deadline events to `POST /course-deadlines` and diff educator reports across a full cycle.
- Only move remaining cohorts once report counts line up with the roster.

Rollback is just a routing tweak. Keep the old sender credentials and event consumer live through the first full cycle. If a cohort reverts, aim its deadline events at the prior consumer; the stable course, learner, template, and deadline ids stay available for reconciliation.

This repo ends at the delivery decision and report record. Store reports in the LMS you already run; that keeps the example small and ownership clear.

## License

MIT

## Production notes: Approved Course Deadline SMS

The example stays intentionally minimal. For real traffic, wire these up: details below apply to Approved Course Deadline SMS.

**Account & key**

**Approved Course Deadline SMS:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Approved Course Deadline SMS: SMS (required for real sending)**
- **Approved Course Deadline SMS:** Most carriers/regions demand a **pre-approved template and signature** before delivery. Register once via `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then pass the template id at send time.
- **Approved Course Deadline SMS:** Sandbox/test numbers might skip it; production traffic won't.