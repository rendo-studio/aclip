# aclip Minimal Specification

## 1. Scope

This specification defines the smallest useful contract for an `aclip`-compatible CLI.

It covers:

- invocation compatibility
- progressive disclosure
- structured runtime envelopes
- credential declaration
- distribution metadata reservation
- machine-readable canonical contracts

It does not yet define:

- registry APIs
- remote download flows
- full auth providers
- PTY, REPL, TUI, or other live-session interaction protocols

## 2. Core rules

### 2.1 Natural invocation

An `aclip` CLI must run like a normal CLI.

Example:

```text
demo-notes note create --title hello --body world
```

The protocol may add disclosure commands, but normal execution cannot depend on them.

### 2.2 Progressive disclosure

An `aclip` CLI must expose:

1. a runtime help index with top-level command groups
2. a runtime help command group view with child commands
3. a runtime help command view with argument-level detail

The standard runtime disclosure surfaces are:

- root help: `<binary> --help`
- command group help: `<binary> <command-group...> --help`
- command help: `<binary> <command...> --help`

Runtime help is rendered as canonical Markdown, not JSON.

The sidecar manifest file `<binary>.aclip.json` remains valid as an offline distribution and registry artifact, but it must not be the only way to discover command usage.

Required runtime forms:

```text
<binary> --help
<binary> <command-group-path...> --help
<binary> <command-path...> --help
```

Runtime help should optimize for immediate agent use, not for registry completeness.

That means runtime help should exclude low-value registration metadata such as:

- binary distribution entries
- registry-only identifiers
- other fields not needed to choose the next command

### 2.3 Interactive boundary

ACLIP standardizes one-shot CLI invocations only.

An ACLIP-compatible CLI may still offer local human features such as a REPL, a TUI, or setup prompts, but those features are outside ACLIP compatibility unless they are also available through normal non-interactive commands.

If a tool needs true live-session interaction, session ownership and control belong to the tool author or an upper-layer protocol.

ACLIP does not require authors to expose session identifiers inside normal business commands or business payloads.

If ACLIP later defines session support, that support should live in a reserved session control plane, not in the author's normal command data shape.

That session control plane remains an optional extension draft, not a core requirement.

### 2.4 Structured envelopes

An `aclip` CLI must emit structured JSON envelopes by default.

Result envelope:

```json
{
  "protocol": "aclip/0.1",
  "type": "result",
  "ok": true,
  "command": "note create",
  "data": {}
}
```

Error envelope:

```json
{
  "protocol": "aclip/0.1",
  "type": "error",
  "ok": false,
  "command": "note create",
  "error": {
    "code": "validation_error",
    "message": "missing required option: --title"
  }
}
```

### 2.5 Traditional exit codes

The CLI must still behave like a normal process:

- `0`: success
- `1`: execution error
- `2`: usage or validation error

### 2.6 Credential declaration

The manifest must support named credential slots.

Each slot declares:

- `name`
- `source`
- `required`
- `description`

Current minimal supported source:

- `env`

Example:

```json
{
  "name": "notes_token",
  "source": "env",
  "envVar": "ACLIP_NOTES_TOKEN",
  "required": false,
  "description": "optional API token for future remote sync"
}
```

### 2.7 Distribution reservation

The manifest must reserve a `distribution` section even if the first milestone only uses local artifacts.

The minimal shape is:

```json
{
  "kind": "standalone_binary",
  "binary": "aclip-demo-notes.exe",
  "platform": "windows-x64",
  "sha256": "..."
}
```

The protocol also reserves a minimal npm distribution form:

```json
{
  "kind": "npm_package",
  "package": "@aclip/demo-notes",
  "version": "0.1.0",
  "executable": "aclip-demo-notes"
}
```

This allows `aclim` and `acli` to build on the same contract later without forcing all adapters into one packaging model.

## 3. Index manifest

The sidecar manifest is the offline discovery and distribution index.

Minimum fields:

```json
{
  "protocol": "aclip/0.1",
  "name": "aclip-demo-notes",
  "version": "0.1.0",
  "summary": "Example notes CLI built with the aclip SDK",
  "description": "Stores notes in a local JSON file and exposes agent-first command disclosure.",
  "command_groups": [
    {
      "path": "note",
      "summary": "Manage notes"
    }
  ],
  "commands": [
    {
      "path": "note create",
      "summary": "Create a note"
    },
    {
      "path": "note list",
      "summary": "List notes"
    }
  ],
  "credentials": [],
  "distribution": []
}
```

The index manifest should stay small enough for first-pass agent discovery.

## 4. Runtime help surfaces

### 4.1 Root help

`<binary> --help` must render canonical Markdown containing:

- tool summary
- tool description
- top-level command groups
- optional top-level commands
- one fixed next-step guidance line

### 4.2 Command group help

`<command-group-path...> --help` must render canonical Markdown containing:

- command group path
- command group summary
- command group description
- immediate child command groups when present
- immediate child commands
- one fixed next-step guidance line

### 4.3 Command help

`<command-path...> --help` must render canonical Markdown containing command-level detail.

Minimum detail fields:

- `path`
- `summary`
- `description`
- `arguments`
- `examples`

Each argument must declare:

- `name`
- `kind`
- `required`
- `position` or `flag`
- `description`

## 5. Compliance levels

### Level 1: Discoverable

- natural invocation
- index manifest
- command detail disclosure

### Level 2: Executable

- all level 1 requirements
- structured result and error envelopes
- traditional exit codes

### Level 3: Portable

- all level 2 requirements
- credential declaration
- distribution metadata

The first repository milestone targets Level 3 for the example CLI.

## 6. Canonical contracts

This repository keeps canonical machine-readable contracts in `schema/`.

Current files:

- `schema/manifest.schema.json`
- `schema/runtime-help-index.schema.json`
- `schema/runtime-help-command-group.schema.json`
- `schema/runtime-help-command.schema.json`
- `schema/result.schema.json`
- `schema/error.schema.json`

Reference adapters must conform to these contracts instead of redefining protocol truth internally.

Protocol truth precedence is:

1. `schema/`
2. protocol documents under `docs/`
3. reference adapters

Adapters may add authoring ergonomics, but they may not fork protocol semantics.

## 7. Runtime Markdown profile

The canonical runtime help format is specified in:

- `docs/PROGRESSIVE-DISCLOSURE-MARKDOWN-SPEC.md`
- `docs/INTERACTIVE-CLI-BOUNDARY.md`
- `docs/SESSION-CONTROL-PLANE.md`

Reference adapters must render runtime help according to that specification instead of inventing local help layouts.

## 8. Cross-language conformance

Reference adapters in different languages must remain semantically equivalent.

That means Python and TypeScript adapters must agree on:

- manifest shape
- runtime help payload shape
- runtime Markdown section order
- result envelope shape
- error envelope shape
- reserved `--help` semantics

Adapter-specific authoring APIs may differ.

Protocol-visible surfaces may not differ.
