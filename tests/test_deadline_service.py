from datetime import datetime, timedelta, timezone

from course_sms.deadline_service import DeadlineRequest, deliver_deadline_notice


class RecordingSender:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def send_batch(self, **values: object) -> dict[str, object]:
        self.calls.append(values)
        return {"data": {"message_id": "sms_course_42"}, "metadata": {}}


def request(deadline: datetime) -> DeadlineRequest:
    return DeadlineRequest(
        course_id="python-101",
        course_name="Python Foundations",
        learner_id="learner-42",
        learner_name="Mina",
        learner_phone="+15551234567",
        educator_id="educator-7",
        deadline=deadline,
    )


def test_deadline_inside_48_hours_uses_approved_copy_and_signature() -> None:
    now = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    sender = RecordingSender()

    report = deliver_deadline_notice(sender, request(now + timedelta(hours=24)), now=now)

    assert report.decision == "sent"
    assert report.message_id == "sms_course_42"
    assert report.signature_id == "brightpath-learning"
    message = sender.calls[0]["messages"][0]  # type: ignore[index]
    assert message["body"].endswith("- BrightPath Learning")
    assert "Python Foundations is due 2026-10-02T09:00+00:00" in message["body"]
    assert sender.calls[0]["idempotency_key"] == (
        "course-deadline:python-101:learner-42:2026-10-02T09:00:00+00:00"
    )


def test_deadline_outside_window_is_reported_without_sending() -> None:
    now = datetime(2026, 10, 1, 9, 0, tzinfo=timezone.utc)
    sender = RecordingSender()

    report = deliver_deadline_notice(sender, request(now + timedelta(days=4)), now=now)

    assert report.decision == "too_early"
    assert report.message_id is None
    assert sender.calls == []

