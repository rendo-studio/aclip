# ACLIP Doctor Control Plane

## 1. Status

This document defines the minimum optional `doctor` control plane for ACLIP.

It is not required for all ACLIP-compatible CLIs.

## 2. Purpose

`doctor` exists to give agents and humans a predictable place to ask:

- what is broken
- what is missing
- what can be fixed automatically

It should not become a generic dumping ground for arbitrary maintenance commands.

## 3. Reserved surface

When a product exposes diagnostics, the reserved top-level command group is:

```text
doctor
```

Recommended baseline commands:

- `doctor check`
- `doctor fix`

## 4. Result shape

Successful doctor output remains author-owned.

For agent-friendly interoperability, the recommended minimum payload shape is:

```json
{
  "checks": [
    {
      "id": "credentials",
      "status": "pass",
      "summary": "required credentials are available"
    }
  ]
}
```

Recommended `checks[]` fields:

- `id`
- `status`
- `summary`

Recommended optional `checks[]` fields:

- `severity`
- `category`
- `hint`
- `remediation`

Recommended status vocabulary:

- `pass`
- `warn`
- `fail`

Recommended severity vocabulary:

- `low`
- `medium`
- `high`
- `critical`

Recommended remediation item shape:

```json
{
  "summary": "login to refresh the credential",
  "command": "notes auth login",
  "automatable": true
}
```

An optional top-level `guidance_md` field may be included when a short Markdown summary or next-step explanation helps the agent.

## 5. Exit codes

- `doctor check`
  - `0` when all checks pass
  - `1` when at least one check fails or warns in a way the author marks as non-healthy
- `doctor fix`
  - `0` when the author-defined fix flow succeeds
  - `1` when the author-defined fix flow fails
- `2` remains reserved for normal usage and validation errors

## 6. Author boundary

ACLIP may provide a skeleton, but authors still own:

- the checks
- the status thresholds
- the fix logic
- any destructive operations
