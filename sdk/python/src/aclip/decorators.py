from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Literal, get_args, get_origin

from .contracts import ArgumentSpec, CommandGroupSpec, CommandHandler, CommandSpec


@dataclass(frozen=True)
class ParsedDocstring:
    summary: str
    description: str
    argument_descriptions: dict[str, str]


class CommandGroupBuilder:
    def __init__(self, app: Any, node: CommandGroupSpec) -> None:
        self._app = app
        self._node = node

    def command(
        self,
        name: str,
        *,
        summary: str | None = None,
        description: str | None = None,
        arguments: list[ArgumentSpec] | None = None,
        examples: list[str] | None = None,
        handler: CommandHandler | None = None,
    ):
        if handler is not None:
            command = command_from_handler(
                name=name,
                handler=handler,
                summary=summary,
                description=description,
                arguments=arguments,
                examples=examples,
            )
            self._node.commands.append(command)
            self._app._refresh_compiled_tree()
            return self

        def decorator(func: Any) -> Any:
            command = command_from_callable(
                name=name,
                func=func,
                summary=summary,
                description=description,
                examples=examples,
            )
            self._node.commands.append(command)
            self._app._refresh_compiled_tree()
            return func

        return decorator

    def group(self, name: str, *, summary: str, description: str) -> "CommandGroupBuilder":
        group = CommandGroupSpec(
            path=(name,),
            summary=summary,
            description=description,
        )
        self._node.command_groups.append(group)
        self._app._refresh_compiled_tree()
        return CommandGroupBuilder(self._app, group)


def command_from_callable(
    *,
    name: str,
    func: Any,
    summary: str | None,
    description: str | None,
    examples: list[str] | None,
) -> CommandSpec:
    parsed = parse_docstring(inspect.getdoc(func) or "")
    command_summary = summary or parsed.summary or _humanize_name(name)
    command_description = description or parsed.description or f"{command_summary}."
    arguments = build_argument_specs(func, parsed.argument_descriptions)

    return CommandSpec(
        path=(name,),
        summary=command_summary,
        description=command_description,
        arguments=arguments,
        examples=list(examples or []),
        handler=_callable_handler(func, arguments),
    )


def command_from_handler(
    *,
    name: str,
    handler: CommandHandler,
    summary: str | None,
    description: str | None,
    arguments: list[ArgumentSpec] | None,
    examples: list[str] | None,
) -> CommandSpec:
    if arguments is None:
        return command_from_callable(
            name=name,
            func=handler,
            summary=summary,
            description=description,
            examples=examples,
        )

    parsed = parse_docstring(inspect.getdoc(handler) or "")
    command_summary = summary or parsed.summary or _humanize_name(name)
    command_description = description or parsed.description or f"{command_summary}."

    return CommandSpec(
        path=(name,),
        summary=command_summary,
        description=command_description,
        arguments=list(arguments),
        examples=list(examples or []),
        handler=_callable_handler(handler, arguments),
    )


def parse_docstring(docstring: str) -> ParsedDocstring:
    if not docstring.strip():
        return ParsedDocstring(summary="", description="", argument_descriptions={})

    lines = [line.rstrip() for line in docstring.splitlines()]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()

    summary_line = lines[0].strip() if lines else ""
    summary = summary_line.rstrip(".")

    description_lines: list[str] = []
    argument_descriptions: dict[str, str] = {}
    in_args = False
    current_arg: str | None = None

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "Args:":
            in_args = True
            current_arg = None
            continue
        if not in_args:
            if stripped:
                description_lines.append(stripped)
            continue

        if not stripped:
            current_arg = None
            continue

        if ":" in stripped and not stripped.startswith("-"):
            arg_name, arg_description = stripped.split(":", 1)
            current_arg = arg_name.strip()
            argument_descriptions[current_arg] = arg_description.strip()
            continue

        if current_arg is not None:
            argument_descriptions[current_arg] = (
                f"{argument_descriptions[current_arg]} {stripped}"
            ).strip()

    description = " ".join(description_lines).strip()
    if not description:
        description = summary_line

    return ParsedDocstring(
        summary=summary,
        description=description,
        argument_descriptions=argument_descriptions,
    )


def build_argument_specs(func: Any, argument_descriptions: dict[str, str]) -> list[ArgumentSpec]:
    signature = inspect.signature(func)
    arguments: list[ArgumentSpec] = []
    for parameter in signature.parameters.values():
        if parameter.kind not in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
        ):
            raise ValueError("unsupported parameter kind for ACLIP decorator authoring")
        metadata = _extract_argument_metadata(parameter.annotation)
        description = argument_descriptions.get(parameter.name, _humanize_name(parameter.name))
        default = None if parameter.default is inspect.Parameter.empty else parameter.default
        required = parameter.default is inspect.Parameter.empty and not metadata["multiple"]
        if metadata["kind"] == "boolean" and parameter.default is inspect.Parameter.empty:
            default = False
            required = False
        arguments.append(
            ArgumentSpec(
                name=parameter.name,
                kind=metadata["kind"],
                description=description if description.endswith(".") else f"{description}.",
                required=required,
                flag=f"--{parameter.name.replace('_', '-')}",
                default=default,
                choices=metadata["choices"],
                multiple=metadata["multiple"],
            )
        )
    return arguments


def _extract_argument_metadata(annotation: Any) -> dict[str, Any]:
    origin = get_origin(annotation)
    args = get_args(annotation)

    if annotation in {inspect.Signature.empty, str}:
        return {"kind": "string", "multiple": False, "choices": None}
    if annotation is int:
        return {"kind": "integer", "multiple": False, "choices": None}
    if annotation is bool:
        return {"kind": "boolean", "multiple": False, "choices": None}

    if origin is Literal:
        literal_values = list(args)
        kind = "integer" if literal_values and all(isinstance(value, int) for value in literal_values) else "string"
        return {"kind": kind, "multiple": False, "choices": [str(value) for value in literal_values]}

    if origin in {list, tuple} and args:
        nested = _extract_argument_metadata(args[0])
        return {
            "kind": nested["kind"],
            "multiple": True,
            "choices": nested["choices"],
        }

    if origin is None and annotation is None:
        return {"kind": "string", "multiple": False, "choices": None}

    return {"kind": "string", "multiple": False, "choices": None}


def _callable_handler(func: Any, arguments: list[ArgumentSpec]):
    argument_names = [argument.name for argument in arguments]

    def handler(payload: dict[str, Any]) -> Any:
        kwargs = {name: payload[name] for name in argument_names if name in payload}
        return func(**kwargs)

    return handler


def _humanize_name(name: str) -> str:
    return name.replace("_", " ").replace("-", " ").capitalize()
