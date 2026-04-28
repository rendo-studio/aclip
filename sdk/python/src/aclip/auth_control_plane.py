from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import CommandGroupSpec, CommandHandler, CommandSpec


AUTH_STATES = {
    "authenticated",
    "unauthenticated",
    "expired",
    "partial",
    "unknown",
}


@dataclass(frozen=True)
class AuthCommandConfig:
    login_description: str
    login_examples: list[str]
    login_handler: CommandHandler = field(repr=False)
    status_description: str
    status_examples: list[str]
    status_handler: CommandHandler = field(repr=False)
    logout_description: str
    logout_examples: list[str]
    logout_handler: CommandHandler = field(repr=False)
    group_summary: str = "Manage authentication"
    group_description: str = "Login, inspect auth state, and logout for the author-defined service."


@dataclass(frozen=True)
class AuthControlPlane:
    command_group: CommandGroupSpec
    commands: list[CommandSpec]


@dataclass(frozen=True)
class AuthNextAction:
    summary: str
    command: str | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"summary": self.summary}
        if self.command is not None:
            payload["command"] = self.command
        return payload


@dataclass(frozen=True)
class AuthStatus:
    state: str
    principal: str | None = None
    expires_at: str | None = None
    missing_credentials: list[str] = field(default_factory=list)
    next_actions: list[AuthNextAction] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.state not in AUTH_STATES:
            raise ValueError(f"unsupported auth state: {self.state}")

    def to_payload(self) -> dict[str, Any]:
        payload = {"state": self.state}
        if self.principal is not None:
            payload["principal"] = self.principal
        if self.expires_at is not None:
            payload["expires_at"] = self.expires_at
        if self.missing_credentials:
            payload["missing_credentials"] = list(self.missing_credentials)
        if self.next_actions:
            payload["next_actions"] = [action.to_payload() for action in self.next_actions]
        return payload


def build_auth_control_plane(config: AuthCommandConfig) -> AuthControlPlane:
    return AuthControlPlane(
        command_group=CommandGroupSpec(
            path=("auth",),
            summary=config.group_summary,
            description=config.group_description,
        ),
        commands=[
            _command(
                ("auth", "login"),
                "Login",
                config.login_description,
                config.login_examples,
                config.login_handler,
            ),
            _command(
                ("auth", "status"),
                "Show auth status",
                config.status_description,
                config.status_examples,
                config.status_handler,
            ),
            _command(
                ("auth", "logout"),
                "Logout",
                config.logout_description,
                config.logout_examples,
                config.logout_handler,
            ),
        ],
    )


def auth_status_result(
    status: AuthStatus | dict[str, Any],
    *,
    guidance_md: str | None = None,
) -> dict[str, Any]:
    payload = status.to_payload() if isinstance(status, AuthStatus) else dict(status)
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
