from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import CommandGroupSpec, CommandHandler, CommandSpec


DOCTOR_CHECK_STATUSES = {
    "pass",
    "warn",
    "fail",
}

DOCTOR_CHECK_SEVERITIES = {
    "low",
    "medium",
    "high",
    "critical",
}


@dataclass(frozen=True)
class DoctorCommandConfig:
    check_description: str
    check_examples: list[str]
    check_handler: CommandHandler = field(repr=False)
    fix_description: str
    fix_examples: list[str]
    fix_handler: CommandHandler = field(repr=False)
    group_summary: str = "Run diagnostics"
    group_description: str = "Inspect the author-defined environment and optionally apply fixes."


@dataclass(frozen=True)
class DoctorControlPlane:
    command_group: CommandGroupSpec
    commands: list[CommandSpec]


@dataclass(frozen=True)
class DoctorRemediation:
    summary: str
    command: str | None = None
    automatable: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"summary": self.summary}
        if self.command is not None:
            payload["command"] = self.command
        if self.automatable is not None:
            payload["automatable"] = self.automatable
        return payload


@dataclass(frozen=True)
class DoctorCheck:
    id: str
    status: str
    summary: str
    severity: str | None = None
    category: str | None = None
    hint: str | None = None
    remediation: list[DoctorRemediation] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.status not in DOCTOR_CHECK_STATUSES:
            raise ValueError(f"unsupported doctor check status: {self.status}")
        if self.severity is not None and self.severity not in DOCTOR_CHECK_SEVERITIES:
            raise ValueError(f"unsupported doctor check severity: {self.severity}")

    def to_payload(self) -> dict[str, Any]:
        payload = {
            "id": self.id,
            "status": self.status,
            "summary": self.summary,
        }
        if self.severity is not None:
            payload["severity"] = self.severity
        if self.category is not None:
            payload["category"] = self.category
        if self.hint is not None:
            payload["hint"] = self.hint
        if self.remediation:
            payload["remediation"] = [item.to_payload() for item in self.remediation]
        return payload


def build_doctor_control_plane(config: DoctorCommandConfig) -> DoctorControlPlane:
    return DoctorControlPlane(
        command_group=CommandGroupSpec(
            path=("doctor",),
            summary=config.group_summary,
            description=config.group_description,
        ),
        commands=[
            _command(
                ("doctor", "check"),
                "Run checks",
                config.check_description,
                config.check_examples,
                config.check_handler,
            ),
            _command(
                ("doctor", "fix"),
                "Apply fixes",
                config.fix_description,
                config.fix_examples,
                config.fix_handler,
            ),
        ],
    )


def doctor_result(
    *,
    checks: list[DoctorCheck | dict[str, Any]],
    guidance_md: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "checks": [
            check.to_payload() if isinstance(check, DoctorCheck) else dict(check)
            for check in checks
        ]
    }
    if guidance_md is not None:
        payload["guidance_md"] = guidance_md
    return payload


def _command(
    path: tuple[str, ...],
    summary: str,
    description: str,
    examples: list[str],
    handler: CommandHandler,
) -> CommandSpec:
    return CommandSpec(
        path=path,
        summary=summary,
        description=description,
        arguments=[],
        examples=examples,
        handler=handler,
    )
