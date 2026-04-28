from __future__ import annotations

from typing import Any

import click

from .contracts import ArgumentSpec, CommandSpec


class ClickParserError(ValueError):
    pass


def translate_argument_spec(argument: ArgumentSpec) -> click.Parameter:
    parameter_type = _click_type(argument)

    if argument.positional:
        return click.Argument(
            param_decls=[argument.name],
            required=argument.required,
            type=parameter_type,
        )

    kwargs: dict[str, Any] = {
        "param_decls": [*argument.resolved_flags(), argument.name],
        "required": argument.required if argument.kind != "boolean" else False,
        "is_flag": argument.kind == "boolean",
        "multiple": argument.multiple,
        "envvar": argument.env_var,
        "help": argument.description,
        "show_default": False,
    }

    if argument.kind != "boolean":
        kwargs["type"] = parameter_type
    if argument.default is not None:
        kwargs["default"] = argument.default

    return click.Option(**kwargs)


def parse_command_arguments(
    *,
    app_name: str,
    commands: list[CommandSpec],
    args: list[str],
) -> tuple[CommandSpec, dict[str, Any]]:
    root = click.Group(name=app_name, commands={}, add_help_option=False)
    group_lookup: dict[tuple[str, ...], click.Group] = {(): root}

    for command in commands:
        parent_path = command.path[:-1]
        for depth in range(1, len(parent_path) + 1):
            group_path = parent_path[:depth]
            if group_path in group_lookup:
                continue

            group = click.Group(
                name=group_path[-1],
                commands={},
                add_help_option=False,
            )
            group_lookup[group_path] = group
            group_lookup[group_path[:-1]].add_command(group)

        parent_group = group_lookup[parent_path]
        parent_group.add_command(_build_click_command(command))

    try:
        return root.main(
            args=args,
            prog_name=app_name,
            standalone_mode=False,
        )
    except click.ClickException as exc:
        raise ClickParserError(exc.format_message()) from exc


def _build_click_command(command: CommandSpec) -> click.Command:
    params = [translate_argument_spec(argument) for argument in command.arguments]

    def callback(**payload: Any) -> tuple[CommandSpec, dict[str, Any]]:
        normalized = {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in payload.items()
        }
        return command, normalized

    return click.Command(
        name=command.path[-1],
        params=params,
        callback=callback,
        add_help_option=False,
    )


def _click_type(argument: ArgumentSpec) -> click.ParamType:
    if argument.choices:
        return click.Choice(argument.choices, case_sensitive=True)
    if argument.kind == "integer":
        return click.INT
    return click.STRING
