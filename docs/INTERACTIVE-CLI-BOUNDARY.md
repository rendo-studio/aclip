# ACLIP Interactive CLI Boundary

## 1. Decision

ACLIP does not standardize a general interactive CLI session protocol.

ACLIP standardizes:

- non-interactive command invocation
- progressive runtime help
- structured result and error envelopes
- credential declaration
- distribution metadata

ACLIP does not standardize:

- PTY or terminal session control
- REPL protocols
- TUI interaction
- stream-oriented stdin/stdout session lifecycles
- attach, detach, interrupt, or resize semantics

## 2. Why this boundary exists

The key question is not whether a CLI looks interactive.

The key question is whether the capability itself depends on a live session.

Many existing CLIs are only pseudo-interactive:

- installers that ask a few questions
- menu-based selection flows
- confirmation prompts
- setup wizards
- local REPL shells that only wrap ordinary subcommands

These flows should be flattened into non-interactive command forms for agents whenever possible.

Examples:

```text
tool install --yes
tool init --name demo --template web --region us-east
tool user create --name alice --role admin
```

For ACLIP, pseudo-interactive flows are a design failure, not a protocol target.

## 3. What counts as true live-session interaction

A capability belongs to the live-session class when most of the useful state exists in a running process and the next input depends on the current streamed output.

Typical examples:

- debugger shells such as `gdb` and `lldb`
- language REPLs such as `python`, `node`, and database shells
- SSH or remote shells
- full-screen terminal applications
- tool-specific agent consoles with long-lived conversation state

These systems usually require some combination of:

- session identifiers
- streamed stdout and stderr reads
- stdin writes over time
- interrupt and termination control
- attach and resume after disconnect

That is not a normal CLI invocation contract anymore. It is a session protocol problem.

## 4. Why ACLIP should not solve this now

Standardizing live-session behavior would force ACLIP to define a much larger surface:

- session creation
- session ownership
- session routing
- process hosting
- buffering and replay
- timeout rules
- interrupt semantics
- security and isolation boundaries

Those concerns belong closer to:

- the tool author
- the session host runtime
- higher-level agent-to-agent or service protocols

They do not belong in the minimal stable core of an agent-native CLI standard.

## 5. Responsibility boundary

If a tool needs long-lived interaction, the tool author should expose it explicitly through a tool-owned surface such as:

- an author-managed session resource
- an HTTP or WebSocket session API
- an A2A-compatible conversation or job handle
- an implementation-specific REPL mode for humans

ACLIP does not define how those sessions work.

At most, ACLIP may later define an optional session control plane extension that standardizes a reserved `session` command group while leaving all storage, lifecycle, routing, and handlers to the author.

## 6. Decision rule

Before adding any interactive requirement to ACLIP, all of the following must be true:

1. The capability cannot be naturally expressed as one-shot subcommands plus flags, files, or resource identifiers.
2. The next action materially depends on streamed live output from a still-running process.
3. The useful state cannot be cleanly externalized into normal resources.
4. The same interaction model is common enough across multiple tools to justify protocol standardization.

If any of those conditions fail, ACLIP should stay non-interactive.

## 7. Current conclusion

The current ACLIP scope remains:

- one-shot command execution
- agent-friendly progressive help
- stable machine-readable envelopes

Interactive session protocols are explicitly out of scope for the current ACLIP line.

For the separate session-oriented direction, see:

- `docs/SESSION-CONTROL-PLANE.md`
