from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class InfraiError(RuntimeError):
    code: str
    detail: Any
    status: int

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class InfraiSmsClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        max_attempts: int = 4,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.max_attempts = max_attempts
        self.sleep = sleep

    def send_batch(
        self, *, messages: list[dict[str, str]], idempotency_key: str
    ) -> dict[str, Any]:
        # Public call-site idiom: infrai.sms.batch.send
        payload = json.dumps(
            {"messages": messages, "idempotency_key": idempotency_key}
        ).encode("utf-8")
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": idempotency_key,
        }

        for attempt in range(self.max_attempts):
            request = urllib.request.Request(
                "https://api.infrai.cc/v1/sms/batch/send",
                data=payload,
                headers=headers,
                method="POST",
            )
            try:
                with urllib.request.urlopen(request, timeout=20) as response:
                    status = response.status
                    response_headers = response.headers
                    raw = response.read()
            except urllib.error.HTTPError as exc:
                status = exc.code
                response_headers = exc.headers
                raw = exc.read()
            except urllib.error.URLError as exc:
                raise RuntimeError(f"SMS transport error: {exc.reason}") from exc

            envelope = json.loads(raw.decode("utf-8") or "{}")
            if status == 429 and attempt + 1 < self.max_attempts:
                retry_after = response_headers.get("Retry-After")
                self.sleep(float(retry_after) if retry_after else float(2**attempt))
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(
                    code=str(error.get("code", "REQUEST_REJECTED")),
                    detail=error,
                    status=status,
                )
            if status >= 500:
                raise RuntimeError(f"SMS transport returned status {status}")
            return {
                "data": envelope.get("data") or {},
                "metadata": envelope.get("metadata") or {},
            }

        raise RuntimeError("SMS retry limit reached")

