from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import os

from course_sms.deadline_service import DeadlineRequest, deliver_deadline_notice
from course_sms.infrai_sms import InfraiSmsClient


phone = os.environ.get("DEMO_PHONE")
if not phone:
    raise SystemExit("DEMO_PHONE is required")

now = datetime.now(timezone.utc)
report = deliver_deadline_notice(
    InfraiSmsClient(),
    DeadlineRequest(
        course_id="python-101",
        course_name="Python Foundations",
        learner_id="learner-42",
        learner_name="Mina",
        learner_phone=phone,
        educator_id="educator-7",
        deadline=now + timedelta(hours=24),
    ),
    now=now,
)
print(json.dumps(asdict(report), indent=2))

