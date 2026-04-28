# ACLIP Workflow Hooks and Skill Export

## Status

The `workflows` draft is intentionally withdrawn.

The earlier attempt to standardize manifest `workflows` metadata and treat it as the canonical intermediate format for skill export was made too early.

## Current decision

- do not treat `workflows` as ACLIP core protocol truth
- continue pursuing skill export as an ACLIP protocol/sdk capability
- use CLI-level and command-level skill export hooks instead of `workflows` as the main model
- keep developer-authored skill package content as the source of truth
- do not reintroduce workflow metadata into core unless it later proves independent value

See [SKILL-EXPORT-HOOKS-VPD.md](D:/project/rendo/aclip/docs/SKILL-EXPORT-HOOKS-VPD.md) for the current reasoning and next-iteration plan.
