# ACLIP Progressive Disclosure Markdown Specification

## 1. Purpose

This document defines the canonical runtime help format for ACLIP-compatible CLIs.

It exists to solve one specific problem:

**how to make `--help` and `<command> --help` simultaneously natural for traditional CLI usage, efficient for agents, and stable enough to be treated as protocol surface instead of ad hoc copywriting.**

This document is protocol-level. It is not implementation guidance for one SDK only.

## 2. Design goals

The runtime help format must satisfy all of the following at the same time:

1. feel natural as modern CLI help
2. support progressive disclosure by depth
3. minimize token waste
4. remain semantically stable for agents
5. support very large command trees and complex commands, including `ffmpeg`-class tools
6. stay readable in plain terminals

## 3. Core position

### 3.1 Progressive disclosure is about staged semantics, not JSON

ACLIP does not require runtime help to be JSON.

The protocol requires:

- stable sections
- stable order
- stable omission rules
- stable wording boundaries

Those properties can be rendered as canonical Markdown.

### 3.2 Schema remains the machine truth source

Runtime Markdown is a rendering layer.

Canonical machine-readable truth remains:

- `schema/`
- sidecar `.aclip.json`
- SDK internal typed models

Therefore:

- machines do not depend on arbitrary prose
- runtime help does not need to carry full registry metadata

## 4. Why Markdown

ACLIP adopts constrained Markdown instead of raw JSON or free-form text because Markdown gives the best tradeoff:

- more natural than JSON
- less ambiguous than arbitrary prose
- easier to chunk than dense plain text
- cheaper in tokens than repeated JSON keys and punctuation
- broadly compatible with terminal, docs, IDEs, and agent UIs

## 5. Markdown profile

ACLIP runtime help uses a **constrained Markdown profile**.

Allowed constructs:

- `#` title
- `##` section headings
- short paragraphs
- flat bullet lists
- fenced code blocks with `text`
- inline code spans

Disallowed constructs:

- tables
- images
- nested lists
- blockquotes
- HTML
- arbitrary heading depth beyond `##`
- free-form long essays

This keeps rendering predictable and parsing simple.

## 6. Required help surfaces

ACLIP defines three runtime help surfaces:

1. root help
2. command group help
3. command help

### 6.1 Root help

Invocation:

```text
tool --help
```

Purpose:

- identify the tool
- describe the top-level capability partition
- give the agent the next most useful expansion targets

Root help must not enumerate all leaf commands of a large CLI.

### 6.2 Command group help

Invocation:

```text
tool <command-group...> --help
```

Purpose:

- describe one command namespace
- list only its immediate child commands
- keep the agent moving down one level

### 6.3 Command help

Invocation:

```text
tool <command...> --help
```

Purpose:

- describe one executable command
- provide usage
- provide argument semantics
- provide examples

## 7. Canonical section order

Section order is fixed.

### 7.1 Root help section order

```md
# <tool-name>

<summary>

<description paragraph>

## Command Groups

- `<group>`: <summary>

## Commands

- `<command>`: <summary>

Next: run `<tool> <path> --help` for one command group or command shown above.
```

If there are no top-level commands, the `## Commands` section is omitted.

### 7.2 Command group help section order

```md
# <group-path>

<summary>

<description paragraph>

## Commands

- `<full command path>`: <summary>
```

If child command groups exist, they appear before `## Commands` as:

```md
## Command Groups

- `<full command-group path>`: <summary>
```

### 7.3 Command help section order

```md
# <command-path>

<description paragraph or summary fallback>

## Usage

```text
tool <command-path> ...
```

## Arguments

- `<argument>` <required|optional>: <description>

## Examples

```text
tool ...
```
```

No additional sections may appear before the canonical sections.

## 8. Required sections and omission rules

### 8.1 Root help

- `summary` must not be omitted
- `description` must not be omitted
- `## Command Groups` must not be omitted
- the fixed `Next:` guidance line must not be omitted

### 8.2 Command group help

- `summary` must not be omitted
- `description` must not be omitted
- `## Commands` must not be omitted

### 8.3 Command help

- `summary` must not be omitted
- `description` must not be omitted
- `## Usage` must not be omitted
- `## Arguments` must not be omitted; if no arguments, write `- None`
- `## Examples` must not be omitted; if no example exists yet, that is a protocol authoring failure

## 9. Content rules

### 9.1 Summary

Summary must be one sentence fragment, not a paragraph.

Good:

- `Create a note`
- `Transcode media streams`

Bad:

- marketing copy
- implementation details
- multiple sentences

### 9.2 Description

Description should answer scope or boundary questions that the summary cannot.

It must stay short:

- root/group: one short paragraph
- command: one short paragraph

For command help rendering, the paragraph shown directly under the title should prefer `description`.
If no description exists, the renderer may fall back to `summary`.

### 9.3 Arguments

Arguments must use this canonical bullet shape:

```md
- `--title <string>` required: Title for the note.
- `--store <string>` optional, default `.notes.json`: Path to the local note store.
```

Rules:

- positional and flag form must be explicit
- required/optional must be explicit
- default must appear only when present
- one bullet per argument
- no nested bullets

### 9.4 Examples

Examples must be real invocations, not placeholders.

Examples should be:

- executable as written
- minimal but representative
- one per line inside a `text` code fence

## 10. Token discipline

ACLIP runtime help should spend tokens only on the agent's next likely action.

Therefore:

- root help shows command groups, not all leaves
- root help may show direct root commands
- command group help shows immediate children, not grandchildren
- command help shows only the current command contract
- registry metadata must stay out of runtime help
- repeated boilerplate must be minimized

## 11. Large CLI strategy

For very large CLIs such as `ffmpeg`-class tools, ACLIP requires decomposition before detail.

That means:

- root help lists major domains only
- each domain becomes a group
- advanced flags should be grouped under narrower command namespaces where possible
- one command help page must not try to document the entire product surface

If a command genuinely has many arguments, the command help page may still be long, but the runtime help hierarchy must ensure the agent reaches that page intentionally rather than by accident.

## 12. Agent parsing expectations

Agents should be able to rely on:

- fixed title line
- fixed section order
- explicit `required` / `optional`
- explicit code-fenced `Usage` and `Examples`
- flat bullet lists for arguments and command listings
- one fixed next-step guidance line on root help

Agents should not need:

- heuristic table parsing
- prose extraction from long essays
- guessing whether a field is mandatory

## 13. Relationship to machine-readable contracts

The runtime Markdown is rendered from structured help data.

That structured help data must continue to conform to canonical schemas under `schema/`.

Therefore:

- Markdown is the runtime presentation layer
- structured contracts remain the protocol truth source

## 14. Non-goals

This spec does not define:

- color
- unicode decorations
- terminal width adaptation
- pager behavior
- registry APIs
- remote execution flows

Those are implementation details unless they affect protocol semantics.

## 15. Implementation consequence

SDKs and adapters must:

1. reserve `--help` and `<command> --help` as protocol surfaces
2. produce structured help data first
3. render canonical Markdown from that data
4. forbid arbitrary help format overrides

Developers may customize content fields.

Developers may not replace the runtime help protocol format.

## 16. Long-term rule

If a future ACLIP implementation must choose between:

- richer formatting
- stricter semantic predictability

it must choose stricter semantic predictability.

That is what keeps the format usable for agents over the next decade.
