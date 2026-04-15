import {
  argumentToManifest,
  createCommandGroupSpec,
  createCommandSpec,
  credentialToManifest,
  distributionToManifest,
  type AppOptions,
  type BuildIndexManifestOptions,
  type CommandGroupRegistration,
  type CommandRegistration,
  type CommandGroupSpec,
  type CommandPayload,
  type CommandSpec,
  type HelpCommandPayload,
  type HelpPayload
} from "./contracts.js";
import { CommanderBackendError, parseCommandArguments } from "./commanderBackend.js";
import { renderHelpMarkdown } from "./renderMarkdown.js";
import { encodeJson, errorEnvelope, resultEnvelope } from "./runtime.js";
import type { CliArtifact } from "./packaging.js";

export interface RunIo {
  stdout: (text: string) => void;
  stderr: (text: string) => void;
}

export class AclipApp {
  readonly name: string;
  readonly version: string;
  readonly summary: string;
  readonly description: string;
  readonly credentials;

  private readonly sourceCommands: CommandSpec[];
  private readonly sourceCommandGroups: CommandGroupSpec[];
  private commands: CommandSpec[];
  private commandGroups: CommandGroupSpec[];

  constructor(options: AppOptions) {
    this.name = options.name;
    this.version = options.version;
    this.summary = options.summary;
    this.description = options.description;
    this.sourceCommands = [...(options.commands ?? [])];
    this.sourceCommandGroups = [...(options.commandGroups ?? [])];
    this.credentials = [...(options.credentials ?? [])];
    const compiled = this.compileAuthoringTree(this.sourceCommands, this.sourceCommandGroups);
    this.commands = compiled.commands;
    this.commandGroups = compiled.commandGroups;
    this.validateProtocolReservedSurfaces();
  }

  command(name: string, registration: CommandRegistration): this {
    this.sourceCommands.push(createCommandSpec(name, registration));
    this.refreshCompiledTree();
    return this;
  }

  group(name: string, registration: CommandGroupRegistration): CommandGroupBuilder {
    const group = createCommandGroupSpec(name, registration);
    this.sourceCommandGroups.push(group);
    this.refreshCompiledTree();
    return new CommandGroupBuilder(group, () => this.refreshCompiledTree());
  }

  buildIndexManifest(options: BuildIndexManifestOptions): Record<string, unknown> {
    return {
      protocol: "aclip/0.1",
      name: options.binaryName,
      version: this.version,
      summary: this.summary,
      description: this.description,
      command_groups: this.commandGroups.map((commandGroup) => ({
        path: commandGroup.path.join(" "),
        summary: commandGroup.summary
      })),
      commands: this.commands.map((command) => ({
        path: command.path.join(" "),
        summary: command.summary
      })),
      credentials: this.credentials.map((credential) => credentialToManifest(credential)),
      distribution: (options.distribution ?? []).map((distribution) => distributionToManifest(distribution))
    };
  }

  buildHelpPayload(pathParts: string[] = []): HelpPayload {
    if (!pathParts.length) {
      const payload: HelpPayload = {
        protocol: "aclip/0.1",
        type: "help_index",
        summary: this.summary,
        description: this.description,
        command_groups: this.commandGroups
          .filter((commandGroup) => commandGroup.path.length === 1)
          .map((commandGroup) => ({
            path: commandGroup.path.join(" "),
            summary: commandGroup.summary
          }))
      };
      const rootCommands = this.commands
        .filter((command) => command.path.length === 1)
        .map((command) => ({
          path: command.path.join(" "),
          summary: command.summary
        }));
      if (rootCommands.length) {
        payload.commands = rootCommands;
      }
      return payload;
    }

    const command = this.findCommand(pathParts);
    if (command) {
      return this.buildCommandDetail(command);
    }

    const group = this.findGroup(pathParts);
    if (!group) {
      throw new Error(`unknown command path: ${pathParts.join(" ")}`);
    }

    const matchingCommands = this.commands
      .filter((candidate) => isDirectChild(candidate.path, pathParts))
      .map((candidate) => ({
        path: candidate.path.join(" "),
        summary: candidate.summary
      }));
    const matchingGroups = this.commandGroups
      .filter((candidate) => isDirectChild(candidate.path, pathParts))
      .map((candidate) => ({
        path: candidate.path.join(" "),
        summary: candidate.summary
      }));

    return {
      protocol: "aclip/0.1",
      type: "help_command_group",
      path: group.path.join(" "),
      summary: group.summary,
      description: group.description,
      command_groups: matchingGroups.length ? matchingGroups : undefined,
      commands: matchingCommands
    };
  }

  async run(argv: string[], io: RunIo = defaultIo()): Promise<number> {
    if (!argv.length) {
      io.stdout(renderHelpMarkdown(this.buildHelpPayload(), this.name));
      return 0;
    }

    const helpFlagIndex = argv.findIndex((token) => token === "--help" || token === "-h");
    if (helpFlagIndex >= 0) {
      const pathParts = argv.slice(0, helpFlagIndex).filter((token) => !token.startsWith("-"));
      try {
        io.stdout(renderHelpMarkdown(this.buildHelpPayload(pathParts), this.name));
        return 0;
      } catch {
        io.stderr(encodeJson(errorEnvelope(pathParts.join(" ") || this.name, "validation_error", "unknown command path for --help")));
        return 2;
      }
    }

    let parsed: { command: CommandSpec; payload: CommandPayload };
    try {
      parsed = await parseCommandArguments(this.commands, argv);
    } catch (error) {
      const message = error instanceof Error ? error.message : "invalid command usage";
      io.stderr(encodeJson(errorEnvelope(argv.slice(0, 2).join(" ") || this.name, "validation_error", message)));
      return 2;
    }

    try {
      const result = await parsed.command.handler(parsed.payload);
      io.stdout(encodeJson(resultEnvelope(parsed.command.path.join(" "), result)));
      return 0;
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      io.stderr(encodeJson(errorEnvelope(parsed.command.path.join(" "), "execution_error", message)));
      return 1;
    }
  }

  async build_cli(options: {
    entryFile: string;
    projectRoot: string;
    outDir?: string;
    executableName?: string;
    packageName?: string;
    packageVersion?: string;
  }): Promise<CliArtifact> {
    const { build_cli } = await import("./packaging.js");
    return build_cli({
      app: this,
      ...options
    });
  }

  private buildCommandDetail(command: CommandSpec): HelpCommandPayload {
    return {
      protocol: "aclip/0.1",
      type: "help_command",
      path: command.path.join(" "),
      summary: command.summary,
      description: command.description,
      usage: this.buildUsage(command),
      arguments: command.arguments.map((argument) => argumentToManifest(argument)),
      examples: [...command.examples]
    };
  }

  private buildUsage(command: CommandSpec): string {
    const parts = [this.name, ...command.path];
    for (const argument of command.arguments) {
      if (argument.positional) {
        parts.push(`<${argument.name}:${argument.kind}>`);
        continue;
      }

      const flag = argument.flag ?? `--${argument.name.replaceAll("_", "-")}`;
      const token = argument.kind === "boolean" ? flag : `${flag} <${argument.kind}>`;

      if (argument.multiple && argument.required) {
        parts.push(`${token}...`);
      } else if (argument.multiple) {
        parts.push(`[${token}]...`);
      } else if (argument.required) {
        parts.push(token);
      } else {
        parts.push(`[${token}]`);
      }
    }
    return parts.join(" ");
  }

  private compileAuthoringTree(
    commands: CommandSpec[],
    commandGroups: CommandGroupSpec[]
  ): { commands: CommandSpec[]; commandGroups: CommandGroupSpec[] } {
    const compiledCommands: CommandSpec[] = [];
    const compiledCommandGroups: CommandGroupSpec[] = [];

    const resolvePath = (path: string[], parent: string[]): string[] =>
      parent.length && path.slice(0, parent.length).every((segment, index) => segment === parent[index])
        ? [...path]
        : [...parent, ...path];

    const compileCommand = (command: CommandSpec, parent: string[]): CommandSpec => ({
      ...command,
      path: resolvePath(command.path, parent),
      arguments: [...command.arguments],
      examples: [...command.examples]
    });

    const visitGroup = (commandGroup: CommandGroupSpec, parent: string[]): void => {
      const resolvedPath = resolvePath(commandGroup.path, parent);
      compiledCommandGroups.push({
        path: resolvedPath,
        summary: commandGroup.summary,
        description: commandGroup.description,
        commands: [],
        commandGroups: []
      });

      commandGroup.commands.forEach((command) => {
        compiledCommands.push(compileCommand(command, resolvedPath));
      });
      commandGroup.commandGroups.forEach((childGroup) => {
        visitGroup(childGroup, resolvedPath);
      });
    };

    commands.forEach((command) => {
      compiledCommands.push(compileCommand(command, []));
    });
    commandGroups.forEach((commandGroup) => {
      visitGroup(commandGroup, []);
    });

    return {
      commands: compiledCommands,
      commandGroups: compiledCommandGroups
    };
  }

  private refreshCompiledTree(): void {
    const compiled = this.compileAuthoringTree(this.sourceCommands, this.sourceCommandGroups);
    this.commands = compiled.commands;
    this.commandGroups = compiled.commandGroups;
    this.validateProtocolReservedSurfaces();
  }

  private validateProtocolReservedSurfaces(): void {
    requireNonEmpty(this.summary, "summary");
    requireNonEmpty(this.description, "description");

    const seenGroupPaths = new Set<string>();
    for (const commandGroup of this.commandGroups) {
      if (!commandGroup.path.length) {
        throw new Error("command groups must have at least one segment");
      }
      requireNonEmpty(commandGroup.summary, "summary");
      requireNonEmpty(commandGroup.description, "description");
      commandGroup.path.forEach((segment) => {
        if (segment.startsWith("-")) {
          throw new Error("command segments cannot start with '-'");
        }
      });
      const key = commandGroup.path.join("\0");
      if (seenGroupPaths.has(key)) {
        throw new Error("duplicate command group path");
      }
      seenGroupPaths.add(key);
    }

    const seenCommandPaths = new Set<string>();
    for (const command of this.commands) {
      requireNonEmpty(command.summary, "summary");
      requireNonEmpty(command.description, "description");
      command.path.forEach((segment) => {
        if (segment.startsWith("-")) {
          throw new Error("command segments cannot start with '-'");
        }
      });
      const key = command.path.join("\0");
      if (seenCommandPaths.has(key)) {
        throw new Error("duplicate command path");
      }
      if (seenGroupPaths.has(key)) {
        throw new Error("command path conflicts with command group path");
      }
      seenCommandPaths.add(key);

      for (const argument of command.arguments) {
        requireNonEmpty(argument.description, "description");
        const resolvedFlag = argument.flag ?? `--${argument.name.replaceAll("_", "-")}`;
        if (!argument.positional && (resolvedFlag === "--help" || resolvedFlag === "-h")) {
          throw new Error("reserved help flag cannot be overridden");
        }
      }

      if (!command.examples.length) {
        throw new Error("examples must contain at least one entry");
      }
      command.examples.forEach((example) => requireNonEmpty(example, "example"));

      if (command.path.length > 1 && !seenGroupPaths.has(command.path.slice(0, -1).join("\0"))) {
        throw new Error("missing command group metadata for command path");
      }
    }
  }

  private findCommand(pathParts: string[]): CommandSpec | undefined {
    return this.commands.find((command) => arraysEqual(command.path, pathParts));
  }

  private findGroup(pathParts: string[]): CommandGroupSpec | undefined {
    return this.commandGroups.find((commandGroup) => arraysEqual(commandGroup.path, pathParts));
  }
}

export class CommandGroupBuilder {
  constructor(
    private readonly node: CommandGroupSpec,
    private readonly onTreeChanged: () => void
  ) {}

  command(name: string, registration: CommandRegistration): this {
    this.node.commands.push(createCommandSpec(name, registration));
    this.onTreeChanged();
    return this;
  }

  group(name: string, registration: CommandGroupRegistration): CommandGroupBuilder {
    const group = createCommandGroupSpec(name, registration);
    this.node.commandGroups.push(group);
    this.onTreeChanged();
    return new CommandGroupBuilder(group, this.onTreeChanged);
  }
}

function defaultIo(): RunIo {
  return {
    stdout: (text) => process.stdout.write(text),
    stderr: (text) => process.stderr.write(text)
  };
}

function requireNonEmpty(value: string, fieldName: string): void {
  if (!value.trim()) {
    throw new Error(`${fieldName} must be a non-empty string`);
  }
}

function arraysEqual(left: string[], right: string[]): boolean {
  return left.length === right.length && left.every((value, index) => value === right[index]);
}

function isDirectChild(candidate: string[], parent: string[]): boolean {
  return candidate.length === parent.length + 1 && parent.every((segment, index) => candidate[index] === segment);
}
