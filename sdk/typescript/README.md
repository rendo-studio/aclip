# @rendo-studio/aclip

`@rendo-studio/aclip` is the canonical TypeScript SDK for ACLIP.

It keeps normal CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- structured result and error envelopes
- sidecar manifests for distribution metadata
- packaging helpers for shipping runnable CLI artifacts

## Install

```bash
npm install @rendo-studio/aclip commander
```

## Smallest End-to-End CLI

`src/app.ts`

```ts
import { AclipApp, stringArgument } from "@rendo-studio/aclip";

export function createApp() {
  const app = new AclipApp({
    name: "notes",
    version: "0.2.0",
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
```

`src/cli.ts`

```ts
import { cliMain } from "@rendo-studio/aclip";

import { createApp } from "./app.js";

void cliMain(createApp);
```

Run it like a normal CLI:

```bash
node --import tsx ./src/cli.ts --help
node --import tsx ./src/cli.ts note --help
node --import tsx ./src/cli.ts note create --help
node --import tsx ./src/cli.ts note create --title hello --body world
```

The final command emits a structured result envelope instead of ad hoc text.

## Build A Distributable CLI

From a dedicated build script:

```ts
import { build_cli } from "@rendo-studio/aclip";

await build_cli({
  appFactory: "./src/app.ts:createApp"
});
```

`appFactory` is the module export that the packaged CLI will execute at runtime.
That is why the recommended pattern is a separate `build.ts` script instead of having the app object “build itself”.

In a conventional project layout, ACLIP infers:

- project root
- package name and version
- executable name

Advanced overrides such as `projectRoot`, `outDir`, `packageName`, and `packageVersion` are still available for monorepos or unusual build layouts, but they are no longer the default path.

## What You Get

- tree-shaped authoring with `AclipApp`, `group()`, and `command()`
- `cliMain(...)` so launchers do not need manual `process.argv.slice(2)`
- canonical ACLIP Markdown help rendering
- structured result and error envelopes
- `build_cli()` as the canonical packaging API

## Repository

- <https://github.com/rendo-studio/aclip>

## Local Verification

```bash
npm test
npm run check
npm run build
```
