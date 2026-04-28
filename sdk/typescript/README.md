# @rendo-studio/aclip

`@rendo-studio/aclip` is the canonical TypeScript SDK for ACLIP.

It keeps normal CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- app-defined success output plus structured error envelopes
- sidecar manifests for distribution metadata
- packaging helpers for shipping runnable CLI artifacts

## Install

```bash
npm install @rendo-studio/aclip
```

## Smallest End-to-End CLI

`main.ts`

```ts
import { AclipApp, stringArgument } from "@rendo-studio/aclip";

export function createApp() {
  const app = new AclipApp({
    name: "notes",
    summary: "A minimal notes CLI.",
    description: "Create and list notes from a small local CLI."
  });

  app.group("note", {
    summary: "Manage notes",
    description: "Create and inspect notes."
  }).command("create", {
    summary: "Create a note",
    description: "Create a note in a local JSON store.",
    arguments: [
      stringArgument("title", { required: true, description: "Title for the note." }),
      stringArgument("body", { required: true, description: "Body text for the note." })
    ],
    examples: ["notes note create --title hello --body world"],
    handler: ({ title, body }) => ({
      note: { title, body }
    })
  });

  return app;
}

export const app = createApp();
```

`cli.ts`

```ts
import { runCli } from "@rendo-studio/aclip";

import { app } from "./main.js";

void runCli(app);
```

If you prefer lazy initialization at process start, the launcher also accepts the factory directly:

```ts
import { runCli } from "@rendo-studio/aclip";

import { createApp } from "./main.js";

void runCli(createApp);
```

Run it like a normal CLI:

```bash
node --import tsx ./cli.ts --help
node --import tsx ./cli.ts note --help
node --import tsx ./cli.ts note create --help
node --import tsx ./cli.ts note create --title hello --body world
```

The final command prints app-defined success output:

- strings stay plain text
- objects and arrays are emitted as plain JSON

`AclipApp.name` is the canonical CLI command token, not a display title. Keep it executable-safe, with no spaces.
`version` is optional during local authoring. Set it before manifest build, packaging, publish, skill export, or the default root `--version` / `-V` / `-v` surface, which prints `<cli-name> <version>`.
`--help` / `-h` remain protocol-reserved discovery flags, while `--version` / `-V` / `-v` are only default root fallbacks and become author-owned again after a concrete command path is selected.
When one author-owned argument should accept multiple aliases, declare `flags: ["--long", "-S"]` instead of splitting aliases across multiple parameters.

## Build A Distributable CLI

From a dedicated build script:

```ts
import * as aclip from "@rendo-studio/aclip";

await aclip.build("./main.ts:app");
```

`build(...)` is the shortest first-class path. `"./main.ts:app"` is the module export that the packaged CLI will execute at runtime.
That is why the recommended pattern is a separate `build.ts` script instead of having the app object “build itself”.

If you prefer to keep initialization behind a function, ACLIP also supports an explicit factory target:

```ts
import { build_cli } from "@rendo-studio/aclip";

await build_cli({
  factory: "./main.ts:createApp"
});
```

If you prefer the fully explicit name, `build_cli(...)` is the same API behind `build(...)`.
For npm packaging, `packageVersion` now defaults to `AclipApp.version`. If `package.json.version` is present and differs, either align the versions or set `packageVersion` explicitly.

## Authentication

ACLIP now standardizes a minimum auth contract around portable credential declarations and an optional reserved `auth` control plane.

```ts
import {
  authStatusResult,
  buildAuthControlPlane,
  envCredential,
  fileCredential
} from "@rendo-studio/aclip";

const credentials = [
  envCredential("notes_token", {
    envVar: "ACLIP_NOTES_TOKEN",
    description: "Remote notes API token.",
    required: true
  }),
  fileCredential("notes_token_file", {
    path: ".secrets/notes-token.txt",
    description: "Optional local token file."
  })
];

const auth = buildAuthControlPlane({
  loginDescription: "Login to the author-defined remote service.",
  loginExamples: ["notes auth login"],
  loginHandler: async () => ({ status: "logged_in" }),
  statusDescription: "Inspect current auth state.",
  statusExamples: ["notes auth status"],
  statusHandler: async () =>
    authStatusResult(
      {
        state: "authenticated",
        principal: "dev@rendo.cn",
        next_actions: [
          {
            summary: "Refresh before expiry",
            command: "notes auth login"
          }
        ]
      },
      {
        guidance_md: "Credential is valid. Refresh before running long-lived jobs."
      }
    ),
  logoutDescription: "Logout from the author-defined remote service.",
  logoutExamples: ["notes auth logout"],
  logoutHandler: async () => ({ status: "logged_out" })
});
```

## Diagnostics

ACLIP also provides a reserved optional `doctor` control plane and helper payload builders for stable agent-facing checks.

```ts
import {
  buildDoctorControlPlane,
  doctorResult
} from "@rendo-studio/aclip";

const doctor = buildDoctorControlPlane({
  checkDescription: "Run author-defined environment checks.",
  checkExamples: ["notes doctor check"],
  checkHandler: async () =>
    doctorResult({
      checks: [
        {
          id: "credentials",
          status: "warn",
          severity: "medium",
          category: "auth",
          summary: "Credential is missing or expired.",
          hint: "Run the login flow before retrying.",
          remediation: [
            {
              summary: "Refresh the credential.",
              command: "notes auth login",
              automatable: true
            }
          ]
        }
      ],
      guidance_md: "Fix the auth check first, then rerun the original command."
    }),
  fixDescription: "Apply author-defined fixes for failed checks.",
  fixExamples: ["notes doctor fix"],
  fixHandler: async () => ({ checks: [] })
});
```

## Export Agent Skills Packages

ACLIP can export developer-authored skill packages while keeping CLI and command metadata aligned as anchors.

There are two different hook scopes:

- `addCliSkill(...)`
  Attach one skill package to the whole CLI.
  Use this for top-level usage strategy, cross-command navigation, auth/doctor preparation, or other whole-tool guidance.
- `addCommandSkill(...)`
  Attach one skill package to one command path.
  Use this for command-specific best practices, prerequisites, recovery steps, or multi-step invocation guidance.

These hooks do **not** change normal runtime behavior.

They do not automatically print skill text when the CLI runs.
They only register export-time linkage so that `export_skills(...)` knows which developer-authored packages to materialize.

```ts
import { export_skills } from "@rendo-studio/aclip";

import { createApp } from "./main.js";

const app = createApp();
app.addCliSkill("./skills/notes-overview");
app.addCommandSkill(["note", "create"], "./skills/note-create-best-practice", {
  metadata: { owner: "docs" }
});

const artifact = await export_skills(app, {
  outDir: "./dist/skills"
});

console.log(artifact.indexPath);
```

What happens here:

1. `app.addCliSkill(...)` registers one whole-CLI package
2. `app.addCommandSkill(...)` registers one command-bound package
3. `export_skills(...)` validates each source package
4. ACLIP copies those packages into the output directory
5. ACLIP injects anchor metadata into `SKILL.md`
6. ACLIP writes a `skills.aclip.json` index beside the exported packages

Each source package must contain a developer-authored `SKILL.md`.

Important boundary:

- hook registration does not install anything into a user workspace
- `export_skills(...)` is an explicit optional API
- if you want `init` or another command to copy exported skills into a project, that copy step is still your command logic, not automatic ACLIP runtime behavior

In a conventional project layout, ACLIP infers:

- project root
- package name and version
- executable name

`src/` is optional. Advanced overrides such as `projectRoot`, `outDir`, `packageName`, and `packageVersion` are still available for monorepos or unusual build layouts, but they are no longer the default path.

## What You Get

- tree-shaped authoring with `AclipApp`, `group()`, and `command()`
- `app.run(...)` for direct execution in tests or custom hosts
- `runCli(...)` for the default launcher path without manual `process.argv.slice(2)`
- canonical ACLIP Markdown help rendering
- app-defined success output plus structured error envelopes
- `build(...)` for the shortest packaging path, with `build_cli(...)` as the explicit equivalent
- `export_skills(...)` for Agent Skills-compatible package export from CLI-level and command-level hooks

## Python vs TypeScript

The Python and TypeScript SDKs now share the same primary story:

- define `app` in `main`
- launch with `run_cli(app)` / `runCli(app)`
- package with `build("main:app")` or `build("./main.ts:app")`

One intentional difference remains: Python also supports `build(create_app)` for a top-level factory function. TypeScript does not expose the same shortcut because a JavaScript function object is not a stable packaging import target on its own.

## Repository

- <https://github.com/rendo-studio/aclip>

## Local Verification

```bash
npm test
npm run check
npm run build
```
