# @rendo-studio/aclip

`@rendo-studio/aclip` is the TypeScript reference adapter for ACLIP.

It is the canonical npm package for building ACLIP-compatible CLIs in TypeScript and Node.js.

ACLIP keeps CLI usage natural while standardizing the parts agents actually depend on:

- progressive Markdown help
- structured result and error envelopes
- sidecar manifests for distribution metadata
- packaging helpers for shipping runnable CLI artifacts

## What it provides

- tree-shaped authoring with `AclipApp`, `group()`, and `command()`
- canonical ACLIP runtime help payloads
- canonical Markdown `--help` rendering
- structured result and error envelopes
- Node-friendly packaging through `build_cli()` and `app.build_cli()`

## Install

```bash
npm install @rendo-studio/aclip commander
```

## First Working CLI

```ts
import { AclipApp, stringArgument } from "@rendo-studio/aclip";

const app = new AclipApp({
  name: "demo",
  version: "0.1.2",
  summary: "Demo CLI",
  description: "Demo CLI."
});

const note = app.group("note", {
  summary: "Manage notes",
  description: "Create and list notes."
});

note
  .command("create", {
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
  })
  .command("list", {
    summary: "List notes",
    description: "List notes from the local JSON store.",
    examples: ["demo note list"],
    handler: () => ({ notes: [] })
  });

const exitCode = await app.run(process.argv.slice(2));
process.exitCode = exitCode;
```

## Packaging

```ts
await app.build_cli({
  entryFile: "./src/cli.ts",
  projectRoot: process.cwd()
});
```

Or use the packaged CLI wrapper:

```bash
aclip-build-cli --app-factory ./src/app.ts:createApp --entry-file ./src/cli.ts
```

This writes:

- a runnable bundled Node CLI artifact
- a sidecar `demo.aclip.json` manifest with `npm_package` distribution metadata

## Typical CLI Usage

```bash
demo --help
demo note --help
demo note create --help
demo note create --title hello --body world
```

## Repository

- <https://github.com/rendo-studio/aclip>

## Local Verification

```bash
npm test
npm run check
npm run build
```
