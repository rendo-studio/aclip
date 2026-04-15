from __future__ import annotations

from aclip import cli_main

from aclip_demo_notes.app import app


def main() -> None:
    cli_main(app)


if __name__ == "__main__":
    main()
