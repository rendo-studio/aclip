# ACLIP Session Control Plane Draft

## 1. Status

This document is a draft for a possible ACLIP extension.

It is not part of the ACLIP core compatibility line yet.

Until ratified, this document should be read as:

- intended shape guidance
- extension design guidance
- SDK skeleton guidance

not as a mandatory core compatibility contract.

## 2. Purpose

This document exists to define the smallest useful standard shape for session-oriented workflows without turning ACLIP into a live terminal protocol.

The problem it tries to solve is narrow:

- some author-built CLIs need resumable agent context across multiple one-shot invocations
- authors should not have to invent a completely different session command surface every time
- ACLIP should not force session identifiers into author business commands or business payloads

## 3. Core position

ACLIP core remains non-interactive.

If a tool needs resumable context, ACLIP may eventually offer an optional **Session Control Plane** extension.

This extension would standardize only:

- the existence of a reserved `session` command group
- the recommended command set inside that group
- the author responsibility boundary
- the recommended lifecycle semantics

It would not standardize:

- PTY hosting
- REPL control
- TUI control
- stream transport
- generic attach or detach semantics
- a universal terminal runtime

## 4. Extension activation rule

This draft is optional.

An ACLIP-compatible CLI does not need to implement any session support unless the author's product genuinely needs resumable context.

If an author does adopt this extension, the recommended shape is:

- reserve a top-level `session` command group
- keep session lifecycle concerns under that group
- keep business commands business-shaped

The extension should remain explicit.

There should be no hidden ambient current-session behavior.

## 5. Responsibility boundary

Session behavior is always author-owned.

ACLIP would only provide standard command group skeletons and default implementation guidance.

Specifically:

- ACLIP may provide default `CommandGroupSpec` and `CommandSpec` examples for session operations
- ACLIP may provide an SDK convenience path to enable those example commands quickly
- ACLIP does not implement the author's session store
- ACLIP does not implement the author's session routing
- ACLIP does not implement the author's session recovery logic
- ACLIP does not define the author's business session state model

Descriptions and handlers remain the author's responsibility.

## 6. Non-goals

This draft does not propose:

- hidden implicit current-session behavior
- mandatory `--session-id` on all business commands
- mandatory `session` fields on all business results
- a universal shell or debugger wrapper
- a shared ACLIP-managed session backend

## 7. Reserved command group

If this extension is adopted, the reserved command group name should be:

```text
session
```

That gives the control plane a stable discovery surface:

```text
tool session --help
tool session create --help
tool session get --help
```

The goal is to keep session concerns out of the author's business command tree as much as possible.

Business commands should stay business-shaped.

Session lifecycle concerns should stay under the reserved control plane.

## 8. Baseline command profile

If this extension is adopted, the default recommended command group should be limited and predictable.

Recommended baseline:

- `session create`
- `session list`
- `session get`
- `session close`

Optional commands, only if the author's product genuinely needs them:

- `session delete`
- `session touch`
- `session exec`

ACLIP should not require every author to implement every command.

The baseline should stay small.

## 9. Default SDK skeleton guidance

ACLIP may eventually provide a convenience skeleton for the reserved command group.

The skeleton should only provide structure, not working business logic.

That means ACLIP may ship example `CommandGroupSpec` and `CommandSpec` definitions like:

```python
CommandGroupSpec(
    path=("session",),
    summary="Manage author-owned sessions",
    description="Create, inspect, list, and close resumable sessions.",
)

CommandSpec(
    path=("session", "create"),
    summary="Create a session",
    description="Create a new author-owned session resource.",
    ...
)
```

But ACLIP should not ship opinionated handlers that pretend to manage the author's real session lifecycle.

The author must still provide:

- descriptions that match the product's real semantics
- handlers that create, inspect, and close the author's sessions
- any persistence, routing, expiry, and cleanup logic

In other words:

- ACLIP may provide the shell
- the author must provide the behavior

## 10. Semantics

### 10.1 `session create`

Purpose:

- create a new author-owned session resource
- return a stable session identifier
- optionally return lifecycle metadata if the author exposes it

### 10.2 `session list`

Purpose:

- enumerate available sessions visible to the current execution context

### 10.3 `session get`

Purpose:

- inspect one session resource and its status

### 10.4 `session close`

Purpose:

- end future use of a session in the author's system

### 10.5 `session delete`

Purpose:

- permanently remove a session resource if the author's product needs destructive cleanup

This should remain optional.

### 10.6 `session touch`

Purpose:

- refresh expiry or keep-alive state if the author's system uses expiring sessions

This should remain optional.

### 10.7 `session exec`

Purpose:

- route one author-defined operation through a session context without forcing the author to expose session identifiers as business arguments

This should remain optional and should only exist when the author's product truly needs a session-aware execution bridge.

## 11. Session identifier rules

If a session identifier exists, ACLIP should treat it as an opaque identifier.

That means:

- clients must not parse its internal structure
- ACLIP does not define its encoding
- ACLIP does not define whether it is local, remote, signed, or database-backed

The author owns all of those choices.

## 12. Session visibility rule

Session use should remain explicit.

That means:

- no hidden global current session
- no protocol-wide requirement that business commands infer a session automatically
- no requirement that every command echo session metadata back

If an author wants session-aware execution, that behavior should be discoverable through explicit session control plane commands and explicit author documentation.

## 13. Recommended lifecycle states

If authors expose lifecycle state, ACLIP should recommend a small portable vocabulary:

- `active`
- `idle`
- `closed`
- `expired`
- `failed`

ACLIP should not require deeper state machines than this.

## 14. Error guidance

If authors expose machine-readable session errors, ACLIP should recommend:

- `session_not_found`
- `session_closed`
- `session_expired`
- `session_conflict`
- `session_unsupported`

These are guidance values, not core requirements yet.

## 15. Recommended disclosure pattern

If an author adopts this extension, progressive help should expose the control plane naturally:

- root help should list `session` as a command group when enabled
- `tool session --help` should describe the available session lifecycle commands
- each implemented session command should disclose usage and examples like any other ACLIP command

This keeps session support aligned with the same progressive disclosure rules as the rest of ACLIP.

## 16. Why this is useful

This extension gives agent-native tools a stable anchor for resumable context while keeping ACLIP out of the business of terminal emulation.

That is useful for:

- tool-internal agent services
- resumable plan execution
- session-oriented remote workflows
- future A2A-aligned command surfaces

## 17. Why this must stay optional

Many ACLIP-compatible CLIs will never need sessions.

For those tools, forcing session support would add useless complexity and permanently pollute the core protocol.

Therefore:

- session control should remain an optional extension
- author-owned implementations should remain valid
- ACLIP core should remain one-shot by default

## 18. Current recommendation

The current repository should treat session support as a documented extension direction, not as a committed core requirement.

The next step, if pursued, should be:

1. define the reserved `session` command group shape
2. define the smallest acceptable command set
3. define an SDK example skeleton
4. avoid touching normal business command payload shapes
