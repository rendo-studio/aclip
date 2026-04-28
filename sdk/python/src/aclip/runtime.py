from __future__ import annotations

import json
from typing import Any

AUTH_ERROR_CODES = {
    "auth_required",
    "invalid_credential",
    "expired_credential",
}


def encode_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True)


def result_envelope(command: str, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        data = {"result": data}
    return {
        "protocol": "aclip/0.1",
        "type": "result",
        "ok": True,
        "command": command,
        "data": data,
    }


def render_success_output(data: Any) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data if data.endswith("\n") else f"{data}\n"
    return f"{encode_json(data)}\n"


def error_envelope(
    command: str,
    code: str,
    message: str,
    *,
    category: str | None = None,
    retryable: bool | None = None,
    hint: str | None = None,
) -> dict[str, Any]:
    error = {
        "code": code,
        "message": message,
    }
    if category is not None:
        error["category"] = category
    if retryable is not None:
        error["retryable"] = retryable
    if hint is not None:
        error["hint"] = hint

    return {
        "protocol": "aclip/0.1",
        "type": "error",
        "ok": False,
        "command": command,
        "error": error,
    }
