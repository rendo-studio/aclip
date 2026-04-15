from __future__ import annotations

import asyncio
import inspect
import sys
from typing import Any

from .click_backend import ClickParserError, parse_command_arguments
from .contracts import CommandGroupSpec, CommandSpec, CredentialSpec, DistributionSpec
from .decorators import CommandGroupBuilder, command_from_callable
from .render_markdown import render_help_markdown
from .runtime import encode_json, error_envelope, result_envelope


class AclipApp:
    def __init__(
        self,
        *,
        name: str,
        version: str,
        summary: str,
        description: str,
        commands: list[CommandSpec] | None = None,
        command_groups: list[CommandGroupSpec] | None = None,
        credentials: list[CredentialSpec] | None = None,
    ) -> None:
        self.name = name
        self.version = version
        self.summary = summary
        self.description = description
        self._source_commands = list(commands or [])
        self._source_command_groups = list(command_groups or [])
        self.commands, self.command_groups = self._compile_authoring_tree(
            commands=self._source_commands,
            command_groups=self._source_command_groups,
        )
        self.credentials = credentials or []
        self._validate_protocol_reserved_surfaces()

    def build_index_manifest(
        self,
        *,
        binary_name: str,
        distribution: list[DistributionSpec] | None = None,
    ) -> dict[str, Any]:
        return {
            "protocol": "aclip/0.1",
            "name": binary_name,
            "version": self.version,
            "summary": self.summary,
            "description": self.description,
            "command_groups": [
                {
                    "path": command_group.group_name(),
                    "summary": command_group.summary,
                }
                for command_group in self.command_groups
            ],
            "commands": [
                {
                    "path": command.command_name(),
                    "summary": command.summary,
                }
                for command in self.commands
            ],
            "credentials": [credential.to_manifest() for credential in self.credentials],
            "distribution": [
                item.to_manifest() for item in (distribution or [])
            ],
        }

    def build_command_detail(self, path_parts: list[str]) -> dict[str, Any]:
        command = self._find_command(path_parts)
        return {
            "protocol": "aclip/0.1",
            "type": "help_command",
            "path": command.command_name(),
            "summary": command.summary,
            "description": command.description,
            "usage": self._build_usage(command),
            "arguments": [argument.to_manifest() for argument in command.arguments],
            "examples": command.examples,
        }

    def build_help_payload(self, path_parts: list[str] | None = None) -> dict[str, Any]:
        parts = path_parts or []
        if not parts:
            payload = {
                "protocol": "aclip/0.1",
                "type": "help_index",
                "summary": self.summary,
                "description": self.description,
                "command_groups": [
                    {
                        "path": command_group.group_name(),
                        "summary": command_group.summary,
                    }
                    for command_group in self.command_groups
                    if len(command_group.path) == 1
                ],
            }
            root_commands = [
                {
                    "path": command.command_name(),
                    "summary": command.summary,
                }
                for command in self.commands
                if len(command.path) == 1
            ]
            if root_commands:
                payload["commands"] = root_commands
            return payload

        try:
            return self.build_command_detail(parts)
        except KeyError:
            group = self._find_group(parts)
            if group is not None:
                matching_commands = [
                    command
                    for command in self.commands
                    if tuple(command.path[: len(parts)]) == tuple(parts)
                    and len(command.path) == len(parts) + 1
                ]
                matching_groups = [
                    child_group
                    for child_group in self.command_groups
                    if tuple(child_group.path[: len(parts)]) == tuple(parts)
                    and len(child_group.path) == len(parts) + 1
                ]
                payload = {
                    "protocol": "aclip/0.1",
                    "type": "help_command_group",
                    "path": group.group_name(),
                    "summary": group.summary,
                    "description": group.description,
                    "commands": [
                        {
                            "path": command.command_name(),
                            "summary": command.summary,
                        }
                        for command in matching_commands
                    ],
                }
                if matching_groups:
                    payload["command_groups"] = [
                        {
                            "path": child_group.group_name(),
                            "summary": child_group.summary,
                        }
                        for child_group in matching_groups
                    ]
                return payload
            raise

    def run(self, argv: list[str] | None = None) -> int:
        args = list(argv if argv is not None else sys.argv[1:])

        if not args:
            print(render_help_markdown(self.build_help_payload(), self.name), end="")
            return 0

        help_flag_index = next(
            (index for index, token in enumerate(args) if token in {"--help", "-h"}),
            None,
        )
        if help_flag_index is not None:
            help_path = [token for token in args[:help_flag_index] if not token.startswith("-")]
            try:
                payload = self.build_help_payload(help_path)
            except KeyError:
                print(
                    encode_json(
                        error_envelope(
                            " ".join(help_path) or self.name,
                            "validation_error",
                            "unknown command path for --help",
                        )
                    ),
                    file=sys.stderr,
                )
                return 2

            print(render_help_markdown(payload, self.name), end="")
            return 0

        try:
            command, payload = parse_command_arguments(
                app_name=self.name,
                commands=self.commands,
                args=args,
            )
        except (SystemExit, ClickParserError) as exc:
            print(
                encode_json(
                    error_envelope(
                        " ".join(args[:2]) if args else self.name,
                        "validation_error",
                        str(exc) if str(exc) else "invalid command usage",
                    )
                ),
                file=sys.stderr,
            )
            return 2

        try:
            result = command.handler(payload)
            if inspect.isawaitable(result):
                result = asyncio.run(result)
        except Exception as exc:  # pragma: no cover - defensive runtime path
            print(
                encode_json(
                    error_envelope(command.command_name(), "execution_error", str(exc))
                ),
                file=sys.stderr,
            )
            return 1

        print(encode_json(result_envelope(command.command_name(), result)))
        return 0

    def command(
        self,
        name: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        examples: list[str] | None = None,
    ):
        def decorator(func: Any) -> Any:
            command = command_from_callable(
                name=name,
                func=func,
                summary=summary,
                description=description,
                examples=examples,
            )
            self._source_commands.append(command)
            self._refresh_compiled_tree()
            return func

        return decorator

    def group(self, name: str, *, summary: str, description: str) -> CommandGroupBuilder:
        group = CommandGroupSpec(
            path=(name,),
            summary=summary,
            description=description,
        )
        self._source_command_groups.append(group)
        self._refresh_compiled_tree()
        return CommandGroupBuilder(self, group)

    def _find_command(self, path_parts: list[str]) -> CommandSpec:
        path = tuple(path_parts)
        for command in self.commands:
            if command.path == path:
                return command
        raise KeyError(f"unknown command path: {' '.join(path_parts)}")

    def _find_group(self, path_parts: list[str]) -> CommandGroupSpec | None:
        path = tuple(path_parts)
        for command_group in self.command_groups:
            if command_group.path == path:
                return command_group
        return None

    def _compile_authoring_tree(
        self,
        *,
        commands: list[CommandSpec],
        command_groups: list[CommandGroupSpec],
    ) -> tuple[list[CommandSpec], list[CommandGroupSpec]]:
        compiled_commands: list[CommandSpec] = []
        compiled_groups: list[CommandGroupSpec] = []

        def normalize_path(path: tuple[str, ...] | str) -> tuple[str, ...]:
            if isinstance(path, str):
                return (path,)
            return tuple(path)

        def resolve_path(path: tuple[str, ...] | str, parent: tuple[str, ...]) -> tuple[str, ...]:
            normalized = normalize_path(path)
            if parent and normalized[: len(parent)] == parent:
                return normalized
            return (*parent, *normalized) if parent else normalized

        def compile_command(command: CommandSpec, parent: tuple[str, ...]) -> CommandSpec:
            return CommandSpec(
                path=resolve_path(command.path, parent),
                summary=command.summary,
                description=command.description,
                arguments=command.arguments,
                examples=command.examples,
                output_schema=command.output_schema,
                output_summary=command.output_summary,
                handler=command.handler,
            )

        def visit_group(command_group: CommandGroupSpec, parent: tuple[str, ...]) -> None:
            resolved_path = resolve_path(command_group.path, parent)
            compiled_groups.append(
                CommandGroupSpec(
                    path=resolved_path,
                    summary=command_group.summary,
                    description=command_group.description,
                )
            )

            for command in command_group.commands:
                compiled_commands.append(compile_command(command, resolved_path))
            for child_group in command_group.command_groups:
                visit_group(child_group, resolved_path)

        for command in commands:
            compiled_commands.append(compile_command(command, ()))
        for command_group in command_groups:
            visit_group(command_group, ())

        return compiled_commands, compiled_groups

    def _refresh_compiled_tree(self) -> None:
        self.commands, self.command_groups = self._compile_authoring_tree(
            commands=self._source_commands,
            command_groups=self._source_command_groups,
        )
        self._validate_protocol_reserved_surfaces()

    def _validate_protocol_reserved_surfaces(self) -> None:
        self._require_non_empty_text(self.summary, "summary")
        self._require_non_empty_text(self.description, "description")

        seen_command_groups: set[tuple[str, ...]] = set()
        for command_group in self.command_groups:
            if not command_group.path:
                raise ValueError("command groups must have at least one segment")
            self._require_non_empty_text(command_group.summary, "summary")
            self._require_non_empty_text(command_group.description, "description")
            for segment in command_group.path:
                if segment.startswith("-"):
                    raise ValueError("command segments cannot start with '-'")
            if command_group.path in seen_command_groups:
                raise ValueError("duplicate command group path")
            seen_command_groups.add(command_group.path)

        seen_commands: set[tuple[str, ...]] = set()
        for command in self.commands:
            self._require_non_empty_text(command.summary, "summary")
            self._require_non_empty_text(command.description, "description")
            for segment in command.path:
                if segment.startswith("-"):
                    raise ValueError("command segments cannot start with '-'")
            if command.path in seen_commands:
                raise ValueError("duplicate command path")
            if command.path in seen_command_groups:
                raise ValueError("command path conflicts with command group path")
            seen_commands.add(command.path)

            for argument in command.arguments:
                self._require_non_empty_text(argument.description, "description")
                resolved_flag = argument.resolved_flag()
                if resolved_flag in {"--help", "-h"}:
                    raise ValueError("reserved help flag cannot be overridden")

            if not command.examples:
                raise ValueError("examples must contain at least one entry")
            for example in command.examples:
                self._require_non_empty_text(example, "example")

            if len(command.path) > 1 and tuple(command.path[:-1]) not in seen_command_groups:
                raise ValueError("missing command group metadata for command path")

    def _build_usage(self, command: CommandSpec) -> str:
        parts = [self.name, *command.path]
        for argument in command.arguments:
            if argument.positional:
                parts.append(f"<{argument.name}:{argument.kind}>")
                continue

            flag = argument.resolved_flag()
            if argument.kind == "boolean":
                token = flag
            else:
                token = f"{flag} <{argument.kind}>"
            if argument.multiple and argument.required:
                parts.append(f"{token}...")
            elif argument.multiple:
                parts.append(f"[{token}]...")
            elif argument.required:
                parts.append(token)
            else:
                parts.append(f"[{token}]")
        return " ".join(parts)

    def _require_non_empty_text(self, value: str, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
