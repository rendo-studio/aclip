from __future__ import annotations

from typing import Any


def render_help_markdown(payload: dict[str, Any], tool_name: str) -> str:
    payload_type = payload["type"]
    if payload_type == "help_index":
        return _render_index(payload, tool_name)
    if payload_type == "help_command_group":
        return _render_group(payload, tool_name)
    if payload_type == "help_command":
        return _render_command(payload)
    raise ValueError(f"unsupported help payload type: {payload_type}")


def _render_index(payload: dict[str, Any], tool_name: str) -> str:
    lines = [
        f"# {tool_name}",
        "",
        payload["summary"],
        "",
    ]
    description = payload.get("description")
    if description:
        lines.extend([description, ""])
    if payload["command_groups"]:
        lines.extend(["## Command Groups", ""])
        for command_group in payload["command_groups"]:
            lines.append(f"- `{command_group['path']}`: {command_group['summary']}")
    if payload.get("commands"):
        if payload["command_groups"]:
            lines.append("")
        lines.extend(["## Commands", ""])
        for command in payload["commands"]:
            lines.append(f"- `{command['path']}`: {command['summary']}")
    lines.extend(
        [
            "",
            _render_next_line(tool_name),
            "",
        ]
    )
    return "\n".join(lines)


def _render_group(payload: dict[str, Any], tool_name: str) -> str:
    lines = [
        f"# {payload['path']}",
        "",
        payload["summary"],
        "",
    ]
    description = payload.get("description")
    if description:
        lines.extend([description, ""])
    if payload.get("command_groups"):
        lines.extend(["## Command Groups", ""])
        for command_group in payload["command_groups"]:
            lines.append(f"- `{command_group['path']}`: {command_group['summary']}")
        lines.append("")
    lines.extend(["## Commands", ""])
    for command in payload["commands"]:
        lines.append(f"- `{command['path']}`: {command['summary']}")
    lines.extend(
        [
            "",
            _render_next_line(tool_name),
            "",
        ]
    )
    return "\n".join(lines)


def _render_command(payload: dict[str, Any]) -> str:
    lines = [
        f"# {payload['path']}",
        "",
        payload["summary"],
        "",
    ]
    description = payload.get("description")
    if description:
        lines.extend([description, ""])

    lines.extend(
        [
            "## Usage",
            "",
            "```text",
            payload["usage"],
            "```",
            "",
            "## Arguments",
            "",
        ]
    )

    arguments = payload["arguments"]
    if not arguments:
        lines.append("- None")
    else:
        for argument in arguments:
            label = _render_argument_label(argument)
            state = "required" if argument["required"] else "optional"
            suffixes: list[str] = []
            if "default" in argument:
                suffixes.append(f"default `{argument['default']}`")
            if argument.get("multiple"):
                suffixes.append("repeatable")
            if "choices" in argument:
                choices = ", ".join(f"`{choice}`" for choice in argument["choices"])
                suffixes.append(f"choices {choices}")
            if "envVar" in argument:
                suffixes.append(f"env `{argument['envVar']}`")
            suffix = f", {', '.join(suffixes)}" if suffixes else ""
            lines.append(
                f"- `{label}` {state}{suffix}: {argument['description']}"
            )

    lines.extend(
        [
            "",
            "## Examples",
            "",
            "```text",
        ]
    )
    for example in payload["examples"]:
        lines.append(example)
    lines.extend(["```", ""])
    return "\n".join(lines)


def _render_argument_label(argument: dict[str, Any]) -> str:
    kind = argument["kind"]
    kind_label = _kind_token(kind)
    if "flag" in argument:
        return f"{argument['flag']} {kind_label}" if kind != "boolean" else argument["flag"]
    if "position" in argument:
        return f"<{argument['position']}:{kind}>"
    return argument["name"]


def _kind_token(kind: str) -> str:
    if kind == "integer":
        return "<integer>"
    if kind == "boolean":
        return ""
    return f"<{kind}>"


def _render_next_line(tool_name: str) -> str:
    if tool_name:
        return f"Next: run `{tool_name} <path> --help` for one command group or command shown above."
    return "Next: run `<tool> <path> --help` for one command group or command shown above."
