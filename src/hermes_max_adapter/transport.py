from __future__ import annotations

import json
from urllib import request as urllib_request
from urllib.error import HTTPError, URLError

from hermes_max_adapter.config import MaxAdapterConfig


class HttpMaxSender:
    def __init__(self, config: MaxAdapterConfig) -> None:
        self.config = config

    def prepare_request(self, request_data: dict) -> dict:
        prepared = dict(request_data)
        prepared["timeout"] = self.config.request_timeout_seconds
        return prepared

    def send(self, request_data: dict) -> dict:
        prepared = self.prepare_request(request_data)
        body = json.dumps(prepared.get("json", {})).encode("utf-8")
        req = urllib_request.Request(
            prepared["url"],
            data=body,
            headers=prepared.get("headers", {}),
            method=prepared.get("method", "POST"),
        )
        try:
            with urllib_request.urlopen(req, timeout=prepared["timeout"]) as response:
                return {
                    "status_code": response.status,
                    "message_id": response.headers.get("X-Message-Id"),
                }
        except HTTPError as exc:
            return {"status_code": exc.code, "error": str(exc)}
        except URLError as exc:
            return {"status_code": 503, "error": str(exc)}
