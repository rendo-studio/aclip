import type { CommandGroupSpec, CommandHandler, CommandSpec } from "./contracts.js";

export const AUTH_STATES = [
  "authenticated",
  "unauthenticated",
  "expired",
  "partial",
  "unknown"
] as const;

export type AuthState = (typeof AUTH_STATES)[number];

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

export interface AuthNextAction {
  summary: string;
  command?: string;
}

export interface AuthStatus {
  state: AuthState;
  principal?: string;
  expires_at?: string;
  missing_credentials?: string[];
  next_actions?: AuthNextAction[];
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

export function authStatusResult(
  status: AuthStatus,
  options: { guidance_md?: string } = {}
): AuthStatus & { guidance_md?: string } {
  if (!AUTH_STATES.includes(status.state)) {
    throw new Error(`unsupported auth state: ${status.state}`);
  }
  return {
    ...status,
    ...(options.guidance_md ? { guidance_md: options.guidance_md } : {})
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
