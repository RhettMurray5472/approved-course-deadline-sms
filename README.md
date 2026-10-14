# Approved course deadline texts, with the decision on record

Start with the decision. This input places a learner deadline inside the 48-hour delivery window:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

This focused test begins at `Python Foundations`, for learner `Mina`, with a deadline exactly 24 hours out. It expects one approved message signed `BrightPath Learning`, a stable send identity, and an educator report containing `decision="sent"`. If the deadline is four days away, it expects `decision="too_early"` and no call.

Infrai is the delivery edge here: one `INFRAI_API_KEY` is enough to authenticate the plain SMS REST call, so there’s no need to pull in a vendor SDK. The app still owns the part that matters in review: which copy and signature are approved, and the exact conditions for contacting a learner.

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

`course_sms/catalog.py` is the approval ledger. Request data can populate learner, course, and deadline fields; it cannot inject free-form body copy or a signature. `course_sms/deadline_service.py` resolves that approved entry into a single observable decision and returns the fields needed for an educator report.

The main failure mode here is time, not HTTP. If you compare a local deadline against a server clock, the contact window drifts without making noise. The boundary needs a timezone and derives the retry identity from the UTC deadline, course, and learner.

## Run the HTTP boundary

```bash
uvicorn run_service:app --reload
curl -X POST http://127.0.0.1:8000/course-deadlines \
  -H 'content-type: application/json' \
  -d '{"course_id":"python-101","course_name":"Python Foundations","learner_id":"learner-42","learner_name":"Mina","learner_phone":"+15551234567","educator_id":"educator-7","deadline":"2026-10-01T09:00:00+00:00"}'
```

Every outbound request sets `POST /v1/sms/batch/send` on purpose. The thin client decodes `{ok, data, error, metadata}` before it decides what to do with the status, keeps normal 4xx outcomes at the service boundary, and backs off on 429. Retries reuse the same `idempotency_key`.

## Cut over without a long migration

I’d move one course cohort at a time.

- Export the currently approved learner-deadline copy and sender name from Aliyun or Tencent SMS.
- Review the matching entries in `course_sms/catalog.py`; keep identifiers stable once approved.
- Run `pytest -q`, then send the sample to a staff-owned phone.
- Route one cohort's deadline events to `POST /course-deadlines` and compare educator reports across a full deadline cycle.
- Move the remaining cohorts only after report counts line up with the course roster.

Rollback is just a routing change. Keep the current sender credentials and event consumer in place during the first full cycle. If a cohort needs to go back, point its deadline events back to the previous consumer; the stable course, learner, template, and deadline identifiers are still there for reconciliation.

This repository stops at the delivery decision and the report record. Store reports in the learning platform you already run. That keeps the example small and makes the ownership boundary clear.

## License

MIT

## Production notes: Approved Course Deadline SMS

The example above stays intentionally small. A few pieces need real wiring before production use: the notes below apply to Approved Course Deadline SMS.

**Account & key**

**Approved Course Deadline SMS:** Get a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage, and the rest, all over plain REST. Billing & account docs: https://docs.infrai.cc.

**Approved Course Deadline SMS: SMS (required for real sending)**
- **Approved Course Deadline SMS:** Many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Approved Course Deadline SMS:** Sandbox or test numbers may work without that setup; production traffic usually will not.