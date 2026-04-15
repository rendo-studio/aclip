from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable


ArgumentKind = str
CommandHandler = Callable[[dict[str, Any]], Any | Awaitable[Any]]


@dataclass(frozen=True)
class ArgumentSpec:
    name: str
    kind: ArgumentKind
    description: str
    required: bool = False
    flag: str | None = None
    positional: bool = False
    default: Any = None
    choices: list[str] | None = None
    multiple: bool = False
    env_var: str | None = None

    def resolved_flag(self) -> str | None:
        if self.positional:
            return None
        return self.flag or f"--{self.name.replace('_', '-')}"

    def to_manifest(self) -> dict[str, Any]:
        payload = {
            "name": self.flag or self.name,
            "kind": self.kind,
            "required": self.required,
            "description": self.description,
        }
        if self.positional:
            payload["position"] = self.name
        else:
            payload["flag"] = self.resolved_flag()
        if self.default is not None:
            payload["default"] = self.default
        if self.choices:
            payload["choices"] = list(self.choices)
        if self.multiple:
            payload["multiple"] = True
        if self.env_var:
            payload["envVar"] = self.env_var
        return payload


@dataclass(frozen=True)
class CredentialSpec:
    name: str
    source: str
    description: str
    required: bool = False
    env_var: str | None = None

    def to_manifest(self) -> dict[str, Any]:
        payload = {
            "name": self.name,
            "source": self.source,
            "required": self.required,
            "description": self.description,
        }
        if self.env_var:
            payload["envVar"] = self.env_var
        return payload


@dataclass(frozen=True)
class DistributionSpec:
    kind: str = "standalone_binary"
    binary: str | None = None
    platform: str | None = None
    sha256: str | None = None
    package: str | None = None
    version: str | None = None
    executable: str | None = None

    @classmethod
    def standalone_binary(
        cls,
        *,
        binary: str,
        platform: str,
        sha256: str,
    ) -> "DistributionSpec":
        return cls(
            kind="standalone_binary",
            binary=binary,
            platform=platform,
            sha256=sha256,
        )

    @classmethod
    def npm_package(
        cls,
        *,
        package: str,
        version: str,
        executable: str,
    ) -> "DistributionSpec":
        return cls(
            kind="npm_package",
            package=package,
            version=version,
            executable=executable,
        )

    def to_manifest(self) -> dict[str, str]:
        if self.kind == "standalone_binary":
            if not self.binary or not self.platform or not self.sha256:
                raise ValueError(
                    "standalone_binary distribution requires binary, platform, and sha256"
                )
            return {
                "kind": self.kind,
                "binary": self.binary,
                "platform": self.platform,
                "sha256": self.sha256,
            }
        if self.kind == "npm_package":
            if not self.package or not self.version or not self.executable:
                raise ValueError(
                    "npm_package distribution requires package, version, and executable"
                )
            return {
                "kind": self.kind,
                "package": self.package,
                "version": self.version,
                "executable": self.executable,
            }
        raise ValueError(f"unsupported distribution kind: {self.kind}")


@dataclass(frozen=True)
class CommandGroupSpec:
    path: tuple[str, ...]
    summary: str
    description: str
    commands: list["CommandSpec"] = field(default_factory=list)
    command_groups: list["CommandGroupSpec"] = field(default_factory=list)

    def group_name(self) -> str:
        return " ".join(self.path)


@dataclass(frozen=True)
class CommandSpec:
    path: tuple[str, ...]
    summary: str
    description: str
    arguments: list[ArgumentSpec]
    examples: list[str]
    handler: CommandHandler = field(repr=False)
    output_schema: dict[str, Any] | None = None
    output_summary: str | None = None

    def command_name(self) -> str:
        return " ".join(self.path)
