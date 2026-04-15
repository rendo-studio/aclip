from __future__ import annotations

import json
from typing import Any


def encode_json(payload: dict[str, Any]) -> str:
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


def error_envelope(command: str, code: str, message: str) -> dict[str, Any]:
    return {
        "protocol": "aclip/0.1",
        "type": "error",
        "ok": False,
        "command": command,
        "error": {
            "code": code,
            "message": message,
        },
    }
