from __future__ import annotations

from typing import Callable

from .app import AclipApp

AppTarget = AclipApp | Callable[[], AclipApp] | str


def resolve_app(target: AppTarget) -> AclipApp:
    if isinstance(target, AclipApp):
        return target

    if isinstance(target, str):
        from .packaging import load_app_factory

        return load_app_factory(target)()

    return target()


def cli_main(target: AppTarget, argv: list[str] | None = None) -> None:
    raise SystemExit(resolve_app(target).run(argv))
