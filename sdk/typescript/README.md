# @aclip/sdk

`@aclip/sdk` is the TypeScript reference adapter for ACLIP.

It does not define the protocol.

It implements the shared ACLIP contracts maintained by the ACLIP repository and provides TypeScript authoring, runtime, and packaging helpers for ACLIP-compatible CLIs.

## What it provides

- tree-shaped authoring with `AclipApp`, `group()`, and `command()`
- canonical ACLIP runtime help payloads
- canonical Markdown `--help` rendering
- structured result and error envelopes
- Node-friendly packaging through `packageNodeCli()`

## Install

```bash
npm install @aclip/sdk commander
```

## Quick Start

```ts
import { AclipApp, stringArgument } from "@aclip/sdk";

const app = new AclipApp({
  name: "demo",
  version: "0.1.0",
  summary: "Demo CLI",
  description: "Demo CLI."
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
    stringArgument("body", { required: true, description: "Body text for the note." })
  ],
  examples: ["demo note create --title hello --body world"],
  handler: ({ title, body }) => ({
    note: { title, body }
  })
});

const exitCode = await app.run(process.argv.slice(2));
process.exitCode = exitCode;
```

## Packaging

```ts
import { packageNodeCli } from "@aclip/sdk";

await packageNodeCli({
  app,
  executableName: "demo",
  packageName: "@aclip/demo",
  packageVersion: "0.1.0",
  entryFile: "./src/cli.ts",
  projectRoot: process.cwd()
});
```

This writes:

- a runnable bundled Node CLI artifact
- a sidecar `demo.aclip.json` manifest with `npm_package` distribution metadata

## Local Verification

```bash
npm test
npm run check
npm run build
```
