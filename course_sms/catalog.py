from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from string import Template
from typing import Mapping


@dataclass(frozen=True)
class ApprovedMessage:
    template_id: str
    signature_id: str
    body: Template


SIGNATURES: Mapping[str, str] = {
    "brightpath-learning": "BrightPath Learning",
}

TEMPLATES: Mapping[str, ApprovedMessage] = {
    "course-deadline-v1": ApprovedMessage(
        template_id="course-deadline-v1",
        signature_id="brightpath-learning",
        body=Template(
            "$learner_name: $course_name is due $deadline. "
            "Open your course workspace to finish."
        ),
    ),
}


def render_approved_deadline(
    *, template_id: str, learner_name: str, course_name: str, deadline: datetime
) -> tuple[str, str]:
    approved = TEMPLATES[template_id]
    signature = SIGNATURES[approved.signature_id]
    content = approved.body.substitute(
        learner_name=learner_name,
        course_name=course_name,
        deadline=deadline.isoformat(timespec="minutes"),
    )
    return f"{content} - {signature}", approved.signature_id

