# @rendo-studio/aclip

`@rendo-studio/aclip` is the canonical TypeScript SDK for ACLIP.

It keeps normal CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- structured result and error envelopes
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
    version: "0.2.3",
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

The final command emits a structured result envelope instead of ad hoc text.

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
- structured result and error envelopes
- `build(...)` for the shortest packaging path, with `build_cli(...)` as the explicit equivalent

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
