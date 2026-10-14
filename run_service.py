from dataclasses import asdict
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from course_sms.deadline_service import DeadlineRequest, deliver_deadline_notice
from course_sms.infrai_sms import InfraiError, InfraiSmsClient


class DeadlineRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: str = Field(min_length=1, max_length=80)
    course_name: str = Field(min_length=1, max_length=100)
    learner_id: str = Field(min_length=1, max_length=80)
    learner_name: str = Field(min_length=1, max_length=60)
    learner_phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$")
    educator_id: str = Field(min_length=1, max_length=80)
    deadline: datetime
    template_id: str = Field(default="course-deadline-v1", min_length=1)


app = FastAPI(title="Approved course deadline SMS")


@app.post("/course-deadlines")
def course_deadline(body: DeadlineRequestBody) -> dict[str, object]:
    deadline = body.deadline
    if deadline.tzinfo is None:
        raise HTTPException(status_code=422, detail="deadline must include a timezone")
    try:
        report = deliver_deadline_notice(
            InfraiSmsClient(),
            DeadlineRequest(**body.model_dump()),
            now=datetime.now(deadline.tzinfo),
        )
        return asdict(report)
    except KeyError as exc:
        raise HTTPException(status_code=422, detail="template_id is not approved") from exc
    except InfraiError as exc:
        caller_status = exc.status if 400 <= exc.status < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "error": exc.detail},
        ) from exc

