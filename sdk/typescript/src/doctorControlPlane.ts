import type { CommandGroupSpec, CommandHandler, CommandSpec } from "./contracts.js";

export const DOCTOR_CHECK_STATUSES = ["pass", "warn", "fail"] as const;
export const DOCTOR_CHECK_SEVERITIES = ["low", "medium", "high", "critical"] as const;

export type DoctorCheckStatus = (typeof DOCTOR_CHECK_STATUSES)[number];
export type DoctorCheckSeverity = (typeof DOCTOR_CHECK_SEVERITIES)[number];

export interface DoctorCommandConfig {
  checkDescription: string;
  checkExamples: string[];
  checkHandler: CommandHandler;
  fixDescription: string;
  fixExamples: string[];
  fixHandler: CommandHandler;
  groupSummary?: string;
  groupDescription?: string;
}

export interface DoctorControlPlane {
  commandGroup: CommandGroupSpec;
  commands: CommandSpec[];
}

export interface DoctorRemediation {
  summary: string;
  command?: string;
  automatable?: boolean;
}

export interface DoctorCheck {
  id: string;
  status: DoctorCheckStatus;
  summary: string;
  severity?: DoctorCheckSeverity;
  category?: string;
  hint?: string;
  remediation?: DoctorRemediation[];
}

export function buildDoctorControlPlane(config: DoctorCommandConfig): DoctorControlPlane {
  return {
    commandGroup: {
      path: ["doctor"],
      summary: config.groupSummary ?? "Run diagnostics",
      description:
        config.groupDescription ??
        "Inspect the author-defined environment and optionally apply fixes.",
      commands: [],
      commandGroups: []
    },
    commands: [
      command(["doctor", "check"], "Run checks", config.checkDescription, config.checkExamples, config.checkHandler),
      command(["doctor", "fix"], "Apply fixes", config.fixDescription, config.fixExamples, config.fixHandler)
    ]
  };
}

export function doctorResult(options: {
  checks: DoctorCheck[];
  guidance_md?: string;
}): { checks: DoctorCheck[]; guidance_md?: string } {
  for (const check of options.checks) {
    if (!DOCTOR_CHECK_STATUSES.includes(check.status)) {
      throw new Error(`unsupported doctor check status: ${check.status}`);
    }
    if (check.severity && !DOCTOR_CHECK_SEVERITIES.includes(check.severity)) {
      throw new Error(`unsupported doctor check severity: ${check.severity}`);
    }
  }

  return {
    checks: options.checks,
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
