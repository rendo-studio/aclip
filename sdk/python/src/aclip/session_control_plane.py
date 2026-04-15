from __future__ import annotations

from dataclasses import dataclass, field

from .contracts import ArgumentSpec, CommandGroupSpec, CommandHandler, CommandSpec


@dataclass(frozen=True)
class SessionCommandConfig:
    summary: str
    description: str
    examples: list[str]
    handler: CommandHandler = field(repr=False)
    output_summary: str | None = None


@dataclass(frozen=True)
class SessionControlPlane:
    command_group: CommandGroupSpec
    commands: list[CommandSpec]


def build_session_control_plane(
    *,
    group_summary: str,
    group_description: str,
    create: SessionCommandConfig,
    list_: SessionCommandConfig,
    get: SessionCommandConfig,
    close: SessionCommandConfig,
    delete: SessionCommandConfig | None = None,
    touch: SessionCommandConfig | None = None,
    exec_: SessionCommandConfig | None = None,
) -> SessionControlPlane:
    commands = [
        _command_without_arguments(("session", "create"), create, _session_object_schema()),
        _command_without_arguments(("session", "list"), list_, _session_list_schema()),
        _command_with_session_id(("session", "get"), get, _session_object_schema()),
        _command_with_session_id(("session", "close"), close, _session_object_schema()),
    ]

    if delete is not None:
        commands.append(
            _command_with_session_id(("session", "delete"), delete, _session_object_schema())
        )

    if touch is not None:
        commands.append(
            _command_with_session_id(("session", "touch"), touch, _session_object_schema())
        )

    if exec_ is not None:
        commands.append(
            CommandSpec(
                path=("session", "exec"),
                summary=exec_.summary,
                description=exec_.description,
                arguments=[
                    _session_id_argument(),
                    ArgumentSpec(
                        name="operation",
                        kind="string",
                        description="Author-defined operation name or token.",
                        positional=True,
                        required=True,
                    ),
                ],
                examples=exec_.examples,
                output_schema=_generic_result_schema(),
                handler=exec_.handler,
            )
        )

    return SessionControlPlane(
        command_group=CommandGroupSpec(
            path=("session",),
            summary=group_summary,
            description=group_description,
        ),
        commands=commands,
    )


def _command_without_arguments(
    path: tuple[str, ...],
    config: SessionCommandConfig,
    output_schema: dict,
) -> CommandSpec:
    return CommandSpec(
        path=path,
        summary=config.summary,
        description=config.description,
        arguments=[],
        examples=config.examples,
        output_schema=output_schema,
        handler=config.handler,
    )


def _command_with_session_id(
    path: tuple[str, ...],
    config: SessionCommandConfig,
    output_schema: dict,
) -> CommandSpec:
    return CommandSpec(
        path=path,
        summary=config.summary,
        description=config.description,
        arguments=[_session_id_argument()],
        examples=config.examples,
        output_schema=output_schema,
        handler=config.handler,
    )


def _session_id_argument() -> ArgumentSpec:
    return ArgumentSpec(
        name="session_id",
        kind="string",
        description="Author-owned session identifier.",
        positional=True,
        required=True,
    )


def _session_object_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "session": {
                "type": "object",
            }
        },
        "required": ["session"],
    }


def _session_list_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "sessions": {
                "type": "array",
                "items": {"type": "object"},
            }
        },
        "required": ["sessions"],
    }


def _generic_result_schema() -> dict:
    return {
        "type": "object",
    }
