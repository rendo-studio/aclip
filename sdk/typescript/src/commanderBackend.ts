import { Command, CommanderError, Option } from "commander";

import type { ArgumentSpec, CommandPayload, CommandSpec } from "./contracts.js";

export class CommanderBackendError extends Error {}

export async function parseCommandArguments(
  commands: CommandSpec[],
  args: string[]
): Promise<{ command: CommandSpec; payload: CommandPayload }> {
  const command = findCommand(commands, args);
  if (!command) {
    throw new CommanderBackendError("unknown command path");
  }

  const remainingArgs = args.slice(command.path.length);
  return {
    command,
    payload: await parseArgumentsForCommand(command, remainingArgs)
  };
}

function findCommand(commands: CommandSpec[], args: string[]): CommandSpec | null {
  const candidates = [...commands].sort((left, right) => right.path.length - left.path.length);
  return candidates.find((command) => command.path.every((segment, index) => args[index] === segment)) ?? null;
}

async function parseArgumentsForCommand(commandSpec: CommandSpec, args: string[]): Promise<CommandPayload> {
  const command = new Command(commandSpec.path.at(-1));
  command.helpOption(false);
  command.allowUnknownOption(false);
  command.allowExcessArguments(false);
  command.exitOverride();
  command.configureOutput({
    writeErr: () => undefined,
    outputError: () => undefined
  });

  const positionalArguments = commandSpec.arguments.filter((argument) => argument.positional);
  const optionArguments = commandSpec.arguments.filter((argument) => !argument.positional);

  for (const argument of positionalArguments) {
    const token = argument.required ? `<${argument.name}>` : `[${argument.name}]`;
    command.argument(token, argument.description, positionalParser(argument), argument.defaultValue as never);
  }

  for (const argument of optionArguments) {
    command.addOption(buildOption(argument));
  }

  try {
    await command.parseAsync(["node", commandSpec.path.join(" "), ...args], {
      from: "node"
    });
  } catch (error) {
    if (error instanceof CommanderError) {
      throw new CommanderBackendError(error.message);
    }
    throw error;
  }

  const options = command.opts<Record<string, unknown>>();
  const payload: CommandPayload = {};

  optionArguments.forEach((argument) => {
    const value = options[argument.name];
    if (value !== undefined) {
      payload[argument.name] = normalizeValue(value);
    }
  });

  positionalArguments.forEach((argument, index) => {
    const value = command.processedArgs[index];
    if (value !== undefined) {
      payload[argument.name] = normalizeValue(value);
    }
  });

  for (const argument of commandSpec.arguments) {
    if (!(argument.name in payload) && argument.defaultValue !== undefined) {
      payload[argument.name] = argument.defaultValue;
    }
    validateChoices(argument, payload[argument.name]);
  }

  return payload;
}

function buildOption(argument: ArgumentSpec): Option {
  const flag = resolveFlag(argument);
  if (!flag) {
    throw new CommanderBackendError("non-positional option must resolve to a flag");
  }

  const flags = argument.kind === "boolean" ? flag : `${flag} ${kindToken(argument.kind)}`;
  const option = new Option(flags, argument.description);

  if (argument.required && argument.kind !== "boolean") {
    option.makeOptionMandatory(true);
  }
  if (argument.envVar) {
    option.env(argument.envVar);
  }
  if (argument.defaultValue !== undefined) {
    option.default(argument.defaultValue);
  }
  if (argument.multiple) {
    option.argParser((value, previous) => {
      const base = Array.isArray(previous) ? previous : [];
      return [...base, convertValue(argument, value)];
    });
    if (argument.defaultValue === undefined) {
      option.default([]);
    }
  } else if (argument.kind !== "boolean") {
    option.argParser((value) => convertValue(argument, value));
  }
  return option;
}

function positionalParser(argument: ArgumentSpec) {
  return (value: string) => convertValue(argument, value);
}

function convertValue(argument: ArgumentSpec, value: unknown): unknown {
  if (argument.kind === "integer") {
    const parsed = Number.parseInt(String(value), 10);
    if (Number.isNaN(parsed)) {
      throw new CommanderBackendError(`invalid integer value for ${argument.name}`);
    }
    return parsed;
  }
  if (argument.kind === "boolean") {
    return Boolean(value);
  }
  return value;
}

function validateChoices(argument: ArgumentSpec, value: unknown): void {
  if (!argument.choices?.length || value === undefined) {
    return;
  }
  if (Array.isArray(value)) {
    for (const item of value) {
      validateChoices(argument, item);
    }
    return;
  }
  if (!argument.choices.includes(String(value))) {
    throw new CommanderBackendError(
      `invalid value for ${argument.name}; expected one of ${argument.choices.join(", ")}`
    );
  }
}

function kindToken(kind: ArgumentSpec["kind"]): string {
  return kind === "integer" ? "<integer>" : "<string>";
}

function resolveFlag(argument: ArgumentSpec): string | null {
  if (argument.positional) {
    return null;
  }
  return argument.flag ?? `--${argument.name.replaceAll("_", "-")}`;
}

function normalizeValue(value: unknown): unknown {
  return Array.isArray(value) ? [...value] : value;
}
