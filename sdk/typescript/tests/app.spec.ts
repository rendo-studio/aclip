import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020";
import { describe, expect, test, vi } from "vitest";

import {
  AclipApp,
  booleanArgument,
  cliMain,
  integerArgument,
  renderHelpMarkdown,
  stringArgument
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
      binaryName: "demo",
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
    expect(app.buildIndexManifest({ binaryName: "demo" }).commands).toEqual([
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

  test("runs commands and emits result envelopes", async () => {
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
    validateAgainstSchema("result", payload);
    expect(payload).toMatchObject({
      protocol: "aclip/0.1",
      type: "result",
      ok: true,
      command: "note create"
    });
    expect(payload.data.note).toMatchObject({
      title: "hello",
      body: "world",
      pinned: true
    });
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

    expect(JSON.parse(writes.join("")).command).toBe("note list");
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

    expect(JSON.parse(writes.join("")).command).toBe("note list");
  });
});
