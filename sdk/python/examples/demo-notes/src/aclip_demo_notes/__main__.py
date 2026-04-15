from __future__ import annotations

from aclip import run_cli

from aclip_demo_notes.app import app


def main() -> None:
    run_cli(app)


if __name__ == "__main__":
    main()
