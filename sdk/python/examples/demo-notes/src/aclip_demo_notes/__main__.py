from __future__ import annotations

import sys

from aclip_demo_notes.app import create_app


def main() -> None:
    raise SystemExit(create_app().run(sys.argv[1:]))


if __name__ == "__main__":
    main()
