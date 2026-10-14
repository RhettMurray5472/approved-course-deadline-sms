from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Literal, Protocol

from .catalog import render_approved_deadline


Decision = Literal["sent", "too_early", "deadline_passed"]


class SmsSender(Protocol):
    def send_batch(
        self, *, messages: list[dict[str, str]], idempotency_key: str
    ) -> dict[str, Any]:
        raise RuntimeError("protocol declaration")


@dataclass(frozen=True)
class DeadlineRequest:
    course_id: str
    course_name: str
    learner_id: str
    learner_name: str
    learner_phone: str
    educator_id: str
    deadline: datetime
    template_id: str = "course-deadline-v1"


@dataclass(frozen=True)
class EducatorReport:
    course_id: str
    learner_id: str
    educator_id: str
    decision: Decision
    template_id: str
    signature_id: str | None
    message_id: str | None


def deliver_deadline_notice(
    sender: SmsSender, request: DeadlineRequest, *, now: datetime
) -> EducatorReport:
    if request.deadline <= now:
        return _report(request, "deadline_passed")
    if request.deadline > now + timedelta(hours=48):
        return _report(request, "too_early")

    body, signature_id = render_approved_deadline(
        template_id=request.template_id,
        learner_name=request.learner_name,
        course_name=request.course_name,
        deadline=request.deadline,
    )
    operation_id = (
        f"course-deadline:{request.course_id}:{request.learner_id}:"
        f"{request.deadline.astimezone(timezone.utc).isoformat()}"
    )
    result = sender.send_batch(
        messages=[{"to": request.learner_phone, "body": body}],
        idempotency_key=operation_id,
    )
    message_id = str(result["data"]["message_id"])
    return EducatorReport(
        course_id=request.course_id,
        learner_id=request.learner_id,
        educator_id=request.educator_id,
        decision="sent",
        template_id=request.template_id,
        signature_id=signature_id,
        message_id=message_id,
    )


def _report(request: DeadlineRequest, decision: Decision) -> EducatorReport:
    return EducatorReport(
        course_id=request.course_id,
        learner_id=request.learner_id,
        educator_id=request.educator_id,
        decision=decision,
        template_id=request.template_id,
        signature_id=None,
        message_id=None,
    )
