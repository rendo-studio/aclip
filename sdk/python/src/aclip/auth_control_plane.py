from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import CommandGroupSpec, CommandHandler, CommandSpec


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
