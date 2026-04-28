import type { HelpCommandGroupPayload, HelpCommandPayload, HelpIndexPayload, HelpPayload } from "./contracts.js";

export function renderHelpMarkdown(payload: HelpPayload, toolName: string): string {
  switch (payload.type) {
    case "help_index":
      return renderIndex(payload, toolName);
    case "help_command_group":
      return renderGroup(payload, toolName);
    case "help_command":
      return renderCommand(payload);
  }
}

function renderIndex(payload: HelpIndexPayload, toolName: string): string {
  const lines = [`# ${toolName}`, "", payload.summary, "", payload.description, ""];

  if (payload.command_groups.length) {
    lines.push("## Command Groups", "");
    for (const commandGroup of payload.command_groups) {
      lines.push(`- \`${commandGroup.path}\`: ${commandGroup.summary}`);
    }
    lines.push("");
  }

  if (payload.commands?.length) {
    lines.push("## Commands", "");
    for (const command of payload.commands) {
      lines.push(`- \`${command.path}\`: ${command.summary}`);
    }
    lines.push("");
  }

  lines.push(nextLine(toolName), "");
  return lines.join("\n");
}

function renderGroup(payload: HelpCommandGroupPayload, toolName: string): string {
  const lines = [`# ${payload.path}`, "", payload.summary, "", payload.description, ""];

  if (payload.command_groups?.length) {
    lines.push("## Command Groups", "");
    for (const commandGroup of payload.command_groups) {
      lines.push(`- \`${commandGroup.path}\`: ${commandGroup.summary}`);
    }
    lines.push("");
  }

  lines.push("## Commands", "");
  for (const command of payload.commands) {
    lines.push(`- \`${command.path}\`: ${command.summary}`);
  }
  lines.push("");
  return lines.join("\n");
}

function renderCommand(payload: HelpCommandPayload): string {
  const description = payload.description || payload.summary;
  const lines = [
    `# ${payload.path}`,
    "",
    description,
    "",
    "## Usage",
    "",
    "```text",
    payload.usage,
    "```",
    "",
    "## Arguments",
    ""
  ];

  if (!payload.arguments.length) {
    lines.push("- None");
  } else {
    for (const argument of payload.arguments) {
      lines.push(renderArgument(argument));
    }
  }

  lines.push("", "## Examples", "", "```text");
  for (const example of payload.examples) {
    lines.push(example);
  }
  lines.push("```", "");
  return lines.join("\n");
}

function renderArgument(argument: Record<string, unknown>): string {
  const kind = String(argument.kind);
  const label = Array.isArray(argument.flags)
    ? kind === "boolean"
      ? argument.flags.map((flag) => String(flag)).join(", ")
      : `${argument.flags.map((flag) => String(flag)).join(", ")} ${kindToken(kind)}`
    : "flag" in argument
      ? kind === "boolean"
        ? String(argument.flag)
        : `${String(argument.flag)} ${kindToken(kind)}`
      : `<${String(argument.position)}:${kind}>`;
  const state = argument.required ? "required" : "optional";
  const suffixes: string[] = [];

  if ("default" in argument) {
    suffixes.push(`default \`${String(argument.default)}\``);
  }
  if (argument.multiple) {
    suffixes.push("repeatable");
  }
  if (Array.isArray(argument.choices)) {
    suffixes.push(`choices ${argument.choices.map((choice) => `\`${String(choice)}\``).join(", ")}`);
  }
  if (typeof argument.envVar === "string") {
    suffixes.push(`env \`${argument.envVar}\``);
  }

  const suffix = suffixes.length ? `, ${suffixes.join(", ")}` : "";
  return `- \`${label}\` ${state}${suffix}: ${String(argument.description)}`;
}

function kindToken(kind: string): string {
  if (kind === "integer") {
    return "<integer>";
  }
  if (kind === "boolean") {
    return "";
  }
  return `<${kind}>`;
}

function nextLine(toolName: string): string {
  return `Next: run \`${toolName} <path> --help\` for one command group or command shown above.`;
}
