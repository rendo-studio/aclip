import type { CommandGroupSpec, CommandHandler, CommandSpec } from "./contracts.js";

export interface AuthCommandConfig {
  loginDescription: string;
  loginExamples: string[];
  loginHandler: CommandHandler;
  statusDescription: string;
  statusExamples: string[];
  statusHandler: CommandHandler;
  logoutDescription: string;
  logoutExamples: string[];
  logoutHandler: CommandHandler;
  groupSummary?: string;
  groupDescription?: string;
}

export interface AuthControlPlane {
  commandGroup: CommandGroupSpec;
  commands: CommandSpec[];
}

export function buildAuthControlPlane(config: AuthCommandConfig): AuthControlPlane {
  return {
    commandGroup: {
      path: ["auth"],
      summary: config.groupSummary ?? "Manage authentication",
      description:
        config.groupDescription ??
        "Login, inspect auth state, and logout for the author-defined service.",
      commands: [],
      commandGroups: []
    },
    commands: [
      command(["auth", "login"], "Login", config.loginDescription, config.loginExamples, config.loginHandler),
      command(
        ["auth", "status"],
        "Show auth status",
        config.statusDescription,
        config.statusExamples,
        config.statusHandler
      ),
      command(["auth", "logout"], "Logout", config.logoutDescription, config.logoutExamples, config.logoutHandler)
    ]
  };
}

function command(
  path: string[],
  summary: string,
  description: string,
  examples: string[],
  handler: CommandHandler
): CommandSpec {
  return {
    path,
    summary,
    description,
    arguments: [],
    examples,
    handler
  };
}
