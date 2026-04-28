import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test, vi } from "vitest";

import {
  AclipApp,
  AUTH_ERROR_CODES,
  AUTH_STATES,
  DOCTOR_CHECK_SEVERITIES,
  DOCTOR_CHECK_STATUSES,
  authStatusResult,
  buildAuthControlPlane,
  buildDoctorControlPlane,
  booleanArgument,
  cliMain,
  doctorResult,
  envCredential,
  fileCredential,
  integerArgument,
  runCli,
  renderHelpMarkdown,
  stringArgument,
  errorEnvelope
} from "../src/index.js";

function loadSchema(name: string) {
  const currentDir = fileURLToPath(new URL(".", import.meta.url));
  const schemaPath = resolve(currentDir, "..", "..", "..", "schema", `${name}.schema.json`);
  return JSON.parse(readFileSync(schemaPath, "utf8"));
}

function validateAgainstSchema(name: string, payload: unknown) {
  const ajv = new Ajv2020({ strict: false });
  const valid = ajv.validate(loadSchema(name), payload);
  expect(valid, JSON.stringify(ajv.errors, null, 2)).toBe(true);
}

function createApp() {
  const app = new AclipApp({
    name: "demo",
    version: "0.1.0",
    summary: "Demo CLI",
    description: "Demo CLI for TypeScript SDK tests."
  });

  app.command("version", {
    summary: "Show version",
    description: "Show the current demo version.",
    examples: ["demo version"],
    handler: () => ({ version: "0.1.0" })
  });

  const note = app.group("note", {
    summary: "Manage notes",
    description: "Create and list notes."
  });

  note.command("create", {
    summary: "Create a note",
    description: "Create a note in a local JSON store.",
    arguments: [
      stringArgument("title", { required: true, description: "Title for the note." }),
      stringArgument("body", { required: true, description: "Body text for the note." }),
      stringArgument("store", {
        description: "Path to the local note store.",
        defaultValue: ".aclip-demo-notes.json"
      }),
      booleanArgument("pinned", {
        description: "Mark the note as pinned."
      }),
      integerArgument("priority", {
        description: "Priority for the note.",
        choices: ["1", "2", "3"]
      })
    ],
    examples: ["demo note create --title hello --body world"],
    handler: (payload) => ({
      note: {
        title: payload.title,
        body: payload.body,
        store: payload.store,
        pinned: payload.pinned,
        priority: payload.priority
      }
    })
  });

  note.command("list", {
    summary: "List notes",
    description: "List notes from the local JSON store.",
    examples: ["demo note list"],
    handler: () => ({ notes: [] })
  });

  return app;
}

describe("AclipApp", () => {
  test("builds schema-compliant manifest and help payloads", () => {
    const app = createApp();

    const manifest = app.buildIndexManifest({
      distribution: [
        {
          kind: "npm_package",
          package: "@aclip/demo",
          version: "0.1.0",
          executable: "demo"
        }
      ]
    });
    const rootPayload = app.buildHelpPayload();
    const groupPayload = app.buildHelpPayload(["note"]);
    const commandPayload = app.buildHelpPayload(["note", "create"]);

    validateAgainstSchema("manifest", manifest);
    validateAgainstSchema("runtime-help-index", rootPayload);
    validateAgainstSchema("runtime-help-command-group", groupPayload);
    validateAgainstSchema("runtime-help-command", commandPayload);

    expect(manifest.command_groups).toEqual([{ path: "note", summary: "Manage notes" }]);
    expect(manifest.commands).toEqual([
      { path: "version", summary: "Show version" },
      { path: "note create", summary: "Create a note" },
      { path: "note list", summary: "List notes" }
    ]);
  });

  test("supports fluent command registration on app and command groups", () => {
    const app = new AclipApp({
      name: "demo",
      version: "0.1.0",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });

    const appResult = app.command("version", {
      summary: "Show version",
      description: "Show the current demo version.",
      examples: ["demo version"],
      handler: () => ({ version: "0.1.0" })
    });

    const note = app.group("note", {
      summary: "Manage notes",
      description: "Create and list notes."
    });

    const groupResult = note.command("create", {
      summary: "Create a note",
      description: "Create a note in a local JSON store.",
      examples: ["demo note create --title hello --body world"],
      handler: () => ({ note: { title: "hello" } })
    }).command("list", {
      summary: "List notes",
      description: "List notes from the local JSON store.",
      examples: ["demo note list"],
      handler: () => ({ notes: [] })
    });

    expect(appResult).toBe(app);
    expect(groupResult).toBe(note);
    expect(app.buildIndexManifest({}).commands).toEqual([
      { path: "version", summary: "Show version" },
      { path: "note create", summary: "Create a note" },
      { path: "note list", summary: "List notes" }
    ]);
  });

  test("renders canonical markdown with next-step guidance", () => {
    const app = createApp();

    const markdown = renderHelpMarkdown(app.buildHelpPayload(), "demo");

    expect(markdown).toBe(
      "# demo\n\n" +
        "Demo CLI\n\n" +
        "Demo CLI for TypeScript SDK tests.\n\n" +
        "## Command Groups\n\n" +
        "- `note`: Manage notes\n\n" +
        "## Commands\n\n" +
        "- `version`: Show version\n\n" +
        "Next: run `demo <path> --help` for one command group or command shown above.\n"
    );
  });

  test("keeps next-step guidance only on root help and avoids repeated command summary lines", () => {
    const app = createApp();

    const groupMarkdown = renderHelpMarkdown(app.buildHelpPayload(["note"]), "demo");
    const commandMarkdown = renderHelpMarkdown(app.buildHelpPayload(["note", "create"]), "demo");

    expect(groupMarkdown).toBe(
      "# note\n\n" +
        "Manage notes\n\n" +
        "Create and list notes.\n\n" +
        "## Commands\n\n" +
        "- `note create`: Create a note\n" +
        "- `note list`: List notes\n"
    );
    expect(commandMarkdown).toBe(
      "# note create\n\n" +
        "Create a note in a local JSON store.\n\n" +
        "## Usage\n\n" +
        "```text\n" +
        "demo note create --title <string> --body <string> [--store <string>] [--pinned] [--priority <integer>]\n" +
        "```\n\n" +
        "## Arguments\n\n" +
        "- `--title <string>` required: Title for the note.\n" +
        "- `--body <string>` required: Body text for the note.\n" +
        "- `--store <string>` optional, default `.aclip-demo-notes.json`: Path to the local note store.\n" +
        "- `--pinned` optional, default `false`: Mark the note as pinned.\n" +
        "- `--priority <integer>` optional, choices `1`, `2`, `3`: Priority for the note.\n\n" +
        "## Examples\n\n" +
        "```text\n" +
        "demo note create --title hello --body world\n" +
        "```\n"
    );
  });

  test("runs commands and preserves app-defined success output", async () => {
    const app = createApp();
    const stdout: string[] = [];
    const stderr: string[] = [];

    const exitCode = await app.run(
      ["note", "create", "--title", "hello", "--body", "world", "--pinned"],
      {
        stdout: (text) => stdout.push(text),
        stderr: (text) => stderr.push(text)
      }
    );

    expect(exitCode).toBe(0);
    expect(stderr).toEqual([]);

    const payload = JSON.parse(stdout.join(""));
    expect(payload.note).toMatchObject({
      title: "hello",
      body: "world",
      pinned: true
    });
    expect(payload).not.toHaveProperty("protocol");
    expect(payload).not.toHaveProperty("ok");
    expect(payload).not.toHaveProperty("command");
  });

  test("returns validation_error envelopes for invalid usage", async () => {
    const app = createApp();
    const stdout: string[] = [];
    const stderr: string[] = [];
    const stderrSpy = vi.spyOn(process.stderr, "write").mockImplementation(() => true);

    try {
      const exitCode = await app.run(["note", "create", "--title", "hello"], {
        stdout: (text) => stdout.push(text),
        stderr: (text) => stderr.push(text)
      });

      expect(exitCode).toBe(2);
      expect(stdout).toEqual([]);

      const payload = JSON.parse(stderr.join(""));
      validateAgainstSchema("error", payload);
      expect(payload.type).toBe("error");
      expect(payload.error.code).toBe("validation_error");
      expect(stderrSpy).not.toHaveBeenCalled();
    } finally {
      stderrSpy.mockRestore();
    }
  });

  test("cliMain uses process argv by default", async () => {
    const app = createApp();
    const originalArgv = process.argv;
    const writes: string[] = [];
    const stdoutSpy = vi.spyOn(process.stdout, "write").mockImplementation(((chunk: string | Uint8Array) => {
      writes.push(String(chunk));
      return true;
    }) as typeof process.stdout.write);

    process.argv = ["node", "demo", "note", "list"];
    try {
      const exitCode = await cliMain(app, undefined);
      expect(exitCode).toBe(0);
    } finally {
      stdoutSpy.mockRestore();
      process.argv = originalArgv;
    }

    expect(JSON.parse(writes.join(""))).toEqual({ notes: [] });
  });

  test("cliMain accepts a string app target", async () => {
    const originalArgv = process.argv;
    const writes: string[] = [];
    const stdoutSpy = vi.spyOn(process.stdout, "write").mockImplementation(((chunk: string | Uint8Array) => {
      writes.push(String(chunk));
      return true;
    }) as typeof process.stdout.write);
    const appTarget = `${resolve(fileURLToPath(new URL(".", import.meta.url)), "..", "examples", "demo-notes", "src", "app.ts")}:app`;

    process.argv = ["node", "demo", "note", "list"];
    try {
      const exitCode = await cliMain(appTarget, undefined);
      expect(exitCode).toBe(0);
    } finally {
      stdoutSpy.mockRestore();
      process.argv = originalArgv;
    }

    expect(JSON.parse(writes.join(""))).toEqual({
      notes: [],
      store: ".aclip-demo-notes.json"
    });
  });

  test("runCli aliases cliMain", () => {
    expect(runCli).toBe(cliMain);
  });

  test("allows scalar success output without result envelopes", async () => {
    const app = new AclipApp({
      name: "demo",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stdout: string[] = [];

    app.command("version", {
      summary: "Show version",
      description: "Show the current demo version.",
      examples: ["demo version"],
      handler: () => "0.1.0"
    });

    const exitCode = await app.run(["version"], {
      stdout: (text) => stdout.push(text),
      stderr: () => undefined
    });

    expect(exitCode).toBe(0);
    expect(stdout.join("")).toBe("0.1.0\n");
  });

  test("allows omitting version until manifest build", async () => {
    const app = new AclipApp({
      name: "demo",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stdout: string[] = [];

    app.command("ping", {
      summary: "Ping",
      description: "Ping something.",
      examples: ["demo ping"],
      handler: () => ({ pong: true })
    });

    const exitCode = await app.run(["ping"], {
      stdout: (text) => stdout.push(text),
      stderr: () => undefined
    });

    expect(exitCode).toBe(0);
    expect(stdout.join("")).toBe("{\"pong\":true}\n");
    expect(() => app.buildIndexManifest({})).toThrow("version is required");
  });

  test("rejects manifest name overrides that diverge from the canonical CLI name", () => {
    const app = new AclipApp({
      name: "demo",
      version: "0.1.0",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });

    expect(() => app.buildIndexManifest({ binaryName: "demo-cli" })).toThrow(
      "binaryName override is no longer supported"
    );
  });

  test("allows a root help command to override the default help alias", async () => {
    const app = new AclipApp({
      name: "demo",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stdout: string[] = [];

    app.command("help", {
      summary: "Custom help",
      description: "Show custom help.",
      examples: ["demo help"],
      handler: () => "custom help"
    });

    const helpCommandExitCode = await app.run(["help"], {
      stdout: (text) => stdout.push(text),
      stderr: () => undefined
    });

    expect(helpCommandExitCode).toBe(0);
    expect(stdout.join("")).toBe("custom help\n");

    stdout.length = 0;

    const helpFlagExitCode = await app.run(["--help"], {
      stdout: (text) => stdout.push(text),
      stderr: () => undefined
    });

    expect(helpFlagExitCode).toBe(0);
    expect(stdout.join("")).toContain("# demo\n\n");
  });

  test("renders root version flags as plain text when configured", async () => {
    const app = new AclipApp({
      name: "demo",
      version: "0.1.0",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stdout: string[] = [];

    expect(
      await app.run(["--version"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("demo 0.1.0\n");

    stdout.length = 0;

    expect(
      await app.run(["-V"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("demo 0.1.0\n");

    stdout.length = 0;

    expect(
      await app.run(["-v"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("demo 0.1.0\n");
  });

  test("returns a validation error for root version flags when version is missing", async () => {
    const app = new AclipApp({
      name: "demo",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stderr: string[] = [];

    const exitCode = await app.run(["--version"], {
      stdout: () => undefined,
      stderr: (text) => stderr.push(text)
    });

    expect(exitCode).toBe(2);
    expect(JSON.parse(stderr.join(""))).toMatchObject({
      error: {
        code: "validation_error",
        message: "version is not configured for this CLI"
      }
    });
  });

  test("treats version aliases as author-owned once a command path is selected", async () => {
    const app = new AclipApp({
      name: "demo",
      version: "0.1.0",
      summary: "Demo CLI",
      description: "Demo CLI for TypeScript SDK tests."
    });
    const stdout: string[] = [];

    app.command("status", {
      summary: "Status",
      description: "Show status.",
      arguments: [booleanArgument("show_version", { flags: ["--version", "-V", "-v"], description: "Show command-owned version state." })],
      examples: ["demo status --version"],
      handler: (payload) => ({ commandVersion: payload.show_version })
    });

    expect(
      await app.run(["status", "--version"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("{\"commandVersion\":true}\n");

    stdout.length = 0;

    expect(
      await app.run(["status", "-V"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("{\"commandVersion\":true}\n");

    stdout.length = 0;

    expect(
      await app.run(["status", "-v"], {
        stdout: (text) => stdout.push(text),
        stderr: () => undefined
      })
    ).toBe(0);
    expect(stdout.join("")).toBe("{\"commandVersion\":true}\n");

    expect(app.buildHelpPayload(["status"])).toMatchObject({
      arguments: [
        {
          flag: "--version",
          flags: ["--version", "-V", "-v"]
        }
      ]
    });
  });

  test("credential helpers support env and file sources", () => {
    expect(
      envCredential("notes_token", {
        envVar: "ACLIP_NOTES_TOKEN",
        description: "Token for remote notes access.",
        required: true
      })
    ).toEqual({
      name: "notes_token",
      source: "env",
      envVar: "ACLIP_NOTES_TOKEN",
      description: "Token for remote notes access.",
      required: true
    });

    expect(
      fileCredential("notes_token_file", {
        path: ".secrets/notes-token.txt",
        description: "Path to a local token file."
      })
    ).toEqual({
      name: "notes_token_file",
      source: "file",
      path: ".secrets/notes-token.txt",
      description: "Path to a local token file.",
      required: false
    });
  });

  test("rejects names that are not CLI tokens", () => {
    expect(
      () =>
        new AclipApp({
          name: "Agent CLI",
          version: "0.1.0",
          summary: "Demo CLI",
          description: "Demo CLI for TypeScript SDK tests."
        })
    ).toThrow("name must be a CLI token");
  });

  test("rejects declaring both flag and flags on one argument", () => {
    expect(
      () =>
        new AclipApp({
          name: "demo",
          version: "0.1.0",
          summary: "Demo CLI",
          description: "Demo CLI for TypeScript SDK tests.",
          commands: [
            {
              path: ["oops"],
              summary: "Oops",
              description: "Oops.",
              arguments: [booleanArgument("mode", { flag: "--mode", flags: ["--mode", "-m"], description: "Oops." })],
              examples: ["demo oops --mode"],
              handler: () => ({ ok: true })
            }
          ]
        })
    ).toThrow("argument cannot declare both flag and flags");
  });

  test("auth error codes are exported", () => {
    expect(AUTH_ERROR_CODES).toEqual([
      "auth_required",
      "invalid_credential",
      "expired_credential"
    ]);
  });

  test("buildAuthControlPlane provides the reserved auth group", () => {
    const controlPlane = buildAuthControlPlane({
      loginDescription: "Login to the author-defined remote service.",
      loginExamples: ["notes auth login"],
      loginHandler: async () => ({ status: "logged_in" }),
      statusDescription: "Inspect current auth state.",
      statusExamples: ["notes auth status"],
      statusHandler: async () => ({ status: "active" }),
      logoutDescription: "Logout from the author-defined remote service.",
      logoutExamples: ["notes auth logout"],
      logoutHandler: async () => ({ status: "logged_out" })
    });

    expect(controlPlane.commandGroup.path).toEqual(["auth"]);
    expect(controlPlane.commands.map((command) => command.path)).toEqual([
      ["auth", "login"],
      ["auth", "status"],
      ["auth", "logout"]
    ]);
  });

  test("errorEnvelope supports richer machine metadata", () => {
    expect(
      errorEnvelope("note sync", "auth_required", "authentication required", {
        category: "auth",
        retryable: false,
        hint: "run `notes auth login` first"
      })
    ).toEqual({
      protocol: "aclip/0.1",
      type: "error",
      ok: false,
      command: "note sync",
      error: {
        code: "auth_required",
        message: "authentication required",
        category: "auth",
        retryable: false,
        hint: "run `notes auth login` first"
      }
    });
  });

  test("buildDoctorControlPlane provides the reserved doctor group", () => {
    const controlPlane = buildDoctorControlPlane({
      checkDescription: "Run author-defined environment checks.",
      checkExamples: ["notes doctor check"],
      checkHandler: async () => ({ checks: [] }),
      fixDescription: "Apply author-defined fixes for failed checks.",
      fixExamples: ["notes doctor fix"],
      fixHandler: async () => ({ checks: [] })
    });

    expect(controlPlane.commandGroup.path).toEqual(["doctor"]);
    expect(controlPlane.commands.map((command) => command.path)).toEqual([
      ["doctor", "check"],
      ["doctor", "fix"]
    ]);
  });

  test("authStatusResult provides a small agent-friendly auth status shape", () => {
    const payload = authStatusResult(
      {
        state: "authenticated",
        principal: "dev@rendo.cn",
        expires_at: "2026-04-21T00:00:00Z",
        next_actions: [{ summary: "Refresh before expiry", command: "notes auth login" }]
      },
      {
        guidance_md:
          "Credential is valid. Refresh before the expiry window if long-running work is expected."
      }
    );

    expect(payload).toEqual({
      state: "authenticated",
      principal: "dev@rendo.cn",
      expires_at: "2026-04-21T00:00:00Z",
      next_actions: [{ summary: "Refresh before expiry", command: "notes auth login" }],
      guidance_md:
        "Credential is valid. Refresh before the expiry window if long-running work is expected."
    });
    expect(AUTH_STATES).toContain("authenticated");
  });

  test("doctorResult provides a stable check vocabulary and optional guidance", () => {
    const payload = doctorResult({
      checks: [
        {
          id: "credentials",
          status: "warn",
          severity: "medium",
          category: "auth",
          summary: "Credential is missing or expired.",
          hint: "Run the auth flow before retrying the command.",
          remediation: [
            {
              summary: "Login to refresh the credential.",
              command: "notes auth login",
              automatable: true
            }
          ]
        }
      ],
      guidance_md: "Fix the auth check first, then rerun the original command."
    });

    expect(payload).toEqual({
      checks: [
        {
          id: "credentials",
          status: "warn",
          severity: "medium",
          category: "auth",
          summary: "Credential is missing or expired.",
          hint: "Run the auth flow before retrying the command.",
          remediation: [
            {
              summary: "Login to refresh the credential.",
              command: "notes auth login",
              automatable: true
            }
          ]
        }
      ],
      guidance_md: "Fix the auth check first, then rerun the original command."
    });
    expect(DOCTOR_CHECK_STATUSES).toContain("warn");
    expect(DOCTOR_CHECK_SEVERITIES).toContain("medium");
  });
});
