export type ArgumentKind = "string" | "integer" | "boolean";

export interface PathSummary {
  path: string;
  summary: string;
}

export interface ArgumentSpec {
  name: string;
  kind: ArgumentKind;
  description: string;
  required?: boolean;
  flag?: string;
  positional?: boolean;
  defaultValue?: unknown;
  choices?: string[];
  multiple?: boolean;
  envVar?: string;
}

export type ArgumentOptions = Omit<ArgumentSpec, "name" | "kind" | "description"> & {
  description?: string;
};

export interface CredentialSpec {
  name: string;
  source: string;
  required: boolean;
  description: string;
  envVar?: string;
}

export interface StandaloneBinaryDistributionSpec {
  kind: "standalone_binary";
  binary: string;
  platform: string;
  sha256: string;
}

export interface NpmPackageDistributionSpec {
  kind: "npm_package";
  package: string;
  version: string;
  executable: string;
}

export type DistributionSpec = StandaloneBinaryDistributionSpec | NpmPackageDistributionSpec;

export type CommandPayload = Record<string, unknown>;
export type CommandHandler = (payload: CommandPayload) => unknown | Promise<unknown>;

export interface CommandSpec {
  path: string[];
  summary: string;
  description: string;
  arguments: ArgumentSpec[];
  examples: string[];
  handler: CommandHandler;
}

export interface CommandGroupSpec {
  path: string[];
  summary: string;
  description: string;
  commands: CommandSpec[];
  commandGroups: CommandGroupSpec[];
}

export interface AppOptions {
  name: string;
  version: string;
  summary: string;
  description: string;
  commands?: CommandSpec[];
  commandGroups?: CommandGroupSpec[];
  credentials?: CredentialSpec[];
}

export interface CommandRegistration {
  summary: string;
  description: string;
  arguments?: ArgumentSpec[];
  examples: string[];
  handler: CommandHandler;
}

export interface CommandGroupRegistration {
  summary: string;
  description: string;
}

export interface BuildIndexManifestOptions {
  binaryName: string;
  distribution?: DistributionSpec[];
}

export interface HelpIndexPayload {
  protocol: "aclip/0.1";
  type: "help_index";
  summary: string;
  description: string;
  command_groups: PathSummary[];
  commands?: PathSummary[];
}

export interface HelpCommandGroupPayload {
  protocol: "aclip/0.1";
  type: "help_command_group";
  path: string;
  summary: string;
  description: string;
  commands: PathSummary[];
  command_groups?: PathSummary[];
}

export interface HelpCommandPayload {
  protocol: "aclip/0.1";
  type: "help_command";
  path: string;
  summary: string;
  description: string;
  usage: string;
  arguments: Array<Record<string, unknown>>;
  examples: string[];
}

export type HelpPayload = HelpIndexPayload | HelpCommandGroupPayload | HelpCommandPayload;

export function resolveFlag(argument: ArgumentSpec): string | null {
  if (argument.positional) {
    return null;
  }
  return argument.flag ?? `--${argument.name.replaceAll("_", "-")}`;
}

export function argumentToManifest(argument: ArgumentSpec): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    name: argument.flag ?? argument.name,
    kind: argument.kind,
    required: Boolean(argument.required),
    description: argument.description
  };

  if (argument.positional) {
    payload.position = argument.name;
  } else {
    payload.flag = resolveFlag(argument);
  }
  if (argument.defaultValue !== undefined) {
    payload.default = argument.defaultValue;
  }
  if (argument.choices?.length) {
    payload.choices = [...argument.choices];
  }
  if (argument.multiple) {
    payload.multiple = true;
  }
  if (argument.envVar) {
    payload.envVar = argument.envVar;
  }
  return payload;
}

export function credentialToManifest(credential: CredentialSpec): Record<string, unknown> {
  return credential.envVar
    ? { ...credential, envVar: credential.envVar }
    : { ...credential };
}

export function distributionToManifest(distribution: DistributionSpec): Record<string, unknown> {
  return { ...distribution };
}

export function stringArgument(
  name: string,
  options: ArgumentOptions = {}
): ArgumentSpec {
  return {
    ...options,
    name,
    kind: "string",
    description: options.description ?? humanizeName(name)
  };
}

export function integerArgument(
  name: string,
  options: ArgumentOptions = {}
): ArgumentSpec {
  return {
    ...options,
    name,
    kind: "integer",
    description: options.description ?? humanizeName(name)
  };
}

export function booleanArgument(
  name: string,
  options: ArgumentOptions = {}
): ArgumentSpec {
  return {
    ...options,
    name,
    kind: "boolean",
    description: options.description ?? humanizeName(name),
    required: false,
    defaultValue: options.defaultValue ?? false
  };
}

export function createCommandGroupSpec(
  name: string,
  registration: CommandGroupRegistration
): CommandGroupSpec {
  return {
    path: [name],
    summary: registration.summary,
    description: registration.description,
    commands: [],
    commandGroups: []
  };
}

export function createCommandSpec(
  name: string,
  registration: CommandRegistration
): CommandSpec {
  return {
    path: [name],
    summary: registration.summary,
    description: registration.description,
    arguments: registration.arguments ?? [],
    examples: [...registration.examples],
    handler: registration.handler
  };
}

function humanizeName(name: string): string {
  const normalized = name.replaceAll("_", " ").replaceAll("-", " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}
