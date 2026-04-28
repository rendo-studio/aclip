# ACLIP Skill Export Hooks VPD

## 1. Status

ACLIP should continue pursuing **skill export**.

This is not generic automatic CLI-to-skill conversion.

The target is export of **Agent Skills-compatible skill packages** from ACLIP-aware authoring hooks, without depending on external tools such as `acli`.

This work belongs in the ACLIP protocol and SDK layer.

The minimum production surface is now implemented in both reference SDKs.

## 2. External alignment

The export target should align with the Agent Skills open format:

- a skill package is a directory with a required `SKILL.md`
- optional support files may live under `scripts/`, `references/`, and `assets/`
- skill activation depends on lightweight metadata plus progressive disclosure of richer content

Reference:

- [What are skills?](https://agentskills.io/what-are-skills)
- [Agent Skills specification](https://agentskills.io/specification)

## 3. VPD basis

This direction meets the VPD bar for two reasons.

### 3.1 Verified current pains

- developers need reusable skill packages, not just better command help
- CLI help and manifests are useful anchors, but they are not enough to represent real skill bodies
- complex commands often need dedicated best-practice guidance around auth, environment setup, recovery paths, and sequencing
- manually keeping ACLIP metadata and skill package metadata aligned is real duplicate work

### 3.2 Deterministic trends

- Agent Skills is an open format with growing client support, so skill-package interoperability is no longer hypothetical
- agent-facing CLIs will keep needing reusable, versioned, auditable procedural knowledge on top of raw command contracts

## 4. What ACLIP should standardize

ACLIP should standardize **skill export hooks**, not full automatic skill generation.

### 4.1 CLI-level skill hooks

CLI-level skill hooks exist for:

- top-level usage strategy
- capability overview
- cross-command navigation
- auth / doctor / environment preparation guidance

These hooks anchor a skill package to the whole CLI surface.

Use a CLI-level hook when the instructions are still useful even if the agent has not committed to one concrete command yet.

Typical cases:

- "how this CLI is organized"
- "which command should be used first"
- "what auth or doctor checks should happen before any write operation"
- "how multiple commands fit into one workflow"

### 4.2 Command-level skill hooks

Command-level skill hooks exist for:

- complex command usage
- multi-step invocation patterns
- prerequisite handling
- failure recovery guidance
- command-specific best practices

These hooks anchor a skill package to one command or command family.

Use a command-level hook when the instructions stop making sense outside a specific command context.

Typical cases:

- "`init` should be run with these prerequisites and flags"
- "`deploy` has a specific recovery path"
- "`sync` requires a sequence of checks before retrying"

### 4.3 Minimum hook shape

The minimum hook shape is now frozen as:

- CLI-level hook:
  - `source_dir`
  - optional free-form `metadata`
- command-level hook:
  - `command_path`
  - `source_dir`
  - optional free-form `metadata`

This keeps ACLIP responsible only for package linkage and metadata alignment, while the developer-owned package directory remains the source of truth.

## 4.4 Runtime boundary

These hooks are **not runtime output hooks**.

They do not:

- change normal command execution
- inject skill text into stdout
- automatically print a skill when a CLI or command runs
- install skill files into a user project during `init`

They only register export-time linkage on `AclipApp`.

The skill package becomes visible only when the developer explicitly calls the export API.

## 4.5 Developer usage flow

The intended usage is:

1. create one or more developer-authored skill package directories
2. attach them to the CLI with:
   - `addCliSkill(...)` for whole-CLI guidance
   - `addCommandSkill(...)` for one command's guidance
3. call `export_skills(...)`
4. ship or copy the exported skill packages wherever the downstream agent runtime expects them

In other words:

- `addCliSkill(...)` and `addCommandSkill(...)` declare linkage
- `export_skills(...)` materializes exported packages
- installation or copying into a real workspace remains author-owned

## 5. What ACLIP metadata should do

ACLIP metadata should act as an **alignment anchor**, not as the complete skill body.

Useful anchor inputs include:

- CLI name, summary, description, version
- command path, summary, description, examples
- auth control-plane linkage
- doctor control-plane linkage
- prerequisite or related-command references

The current exported metadata anchors are:

- `aclip-hook-kind`
- `aclip-cli-name`
- `aclip-cli-version`
- optional `aclip-auth-group`
- optional `aclip-doctor-group`
- for command hooks:
  - `aclip-command-path`
  - `aclip-command-summary`
  - `aclip-command-description`

These help ACLIP export packages that stay aligned with the CLI surface and remain discoverable to agents.

This metadata is injected during export.

It is not emitted during normal CLI execution.

## 6. What developers must still own

The developer should remain responsible for the substantive contents of the skill package, including:

- the main `SKILL.md` instructions body
- skill-specific scripts
- reference documents
- assets and templates
- task strategy, examples, and recovery guidance

ACLIP should not pretend that command help is enough to auto-write these well.

## 7. What ACLIP should not standardize

ACLIP should not:

- treat `workflows` as protocol truth for skill export
- require `acli` or another external CLI as the export engine
- assume full automatic generation of skill bodies from command metadata alone
- collapse skill export into a generic interoperability adapter problem

ACLIP should also not overwrite the developer-authored body of the skill package beyond frontmatter normalization and injected anchor metadata.

ACLIP should also not pretend that hook registration by itself means the package is already installed anywhere.

## 8. Workflows status

The previous `workflows` direction remains withdrawn as protocol truth.

Current position:

- `workflows` are not required for skill export
- `workflows` are not the canonical intermediate model
- `workflows` may only return later if they prove independent value inside the build pipeline

## 9. Implemented minimum milestone

The current ACLIP skill-export milestone now covers:

1. CLI-level skill package hooks
2. command-level skill package hooks
3. metadata alignment between ACLIP surfaces and Agent Skills package metadata
4. developer-authored skill package handoff into exported packages
5. package export validation for required `SKILL.md` frontmatter and package indexing via `skills.aclip.json`

## 10. Remaining future questions

The following are still future-facing questions, not blockers for the minimum surface:

- whether one command should map to multiple exported packages in first-class SDK helpers
- whether richer prerequisite linkage should get its own typed field beyond free-form metadata
- how far ACLIP should go in validating optional `scripts/`, `references/`, and `assets/` contents
