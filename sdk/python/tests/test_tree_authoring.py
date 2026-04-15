from aclip import AclipApp, CommandGroupSpec, CommandSpec


def _leaf(path: tuple[str, ...], summary: str) -> CommandSpec:
    return CommandSpec(
        path=path,
        summary=summary,
        description=f"{summary}.",
        arguments=[],
        examples=[f"demo {' '.join(path)}"],
        output_schema={"type": "object"},
        output_summary=f"Returns a result for {summary.lower()}.",
        handler=lambda _args: {"ok": True},
    )


def test_nested_tree_authoring_compiles_to_flat_manifest_paths():
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI with tree authoring.",
        commands=[
            _leaf(("version",), "Show version"),
        ],
        command_groups=[
            CommandGroupSpec(
                path=("note",),
                summary="Manage notes",
                description="Manage notes.",
                commands=[
                    _leaf(("create",), "Create a note"),
                    _leaf(("list",), "List notes"),
                ],
                command_groups=[
                    CommandGroupSpec(
                        path=("admin",),
                        summary="Admin note operations",
                        description="Admin note operations.",
                        commands=[
                            _leaf(("prune",), "Prune notes"),
                        ],
                    ),
                ],
            ),
        ],
    )

    manifest = app.build_index_manifest(binary_name="demo")
    root_payload = app.build_help_payload()

    assert manifest["commands"] == [
        {"path": "version", "summary": "Show version"},
        {"path": "note create", "summary": "Create a note"},
        {"path": "note list", "summary": "List notes"},
        {"path": "note admin prune", "summary": "Prune notes"},
    ]
    assert manifest["command_groups"] == [
        {"path": "note", "summary": "Manage notes"},
        {"path": "note admin", "summary": "Admin note operations"},
    ]
    assert root_payload["command_groups"] == [
        {"path": "note", "summary": "Manage notes"},
    ]
    assert root_payload["commands"] == [
        {"path": "version", "summary": "Show version"},
    ]


def test_group_help_payload_can_disclose_child_groups_and_child_commands():
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI with tree authoring.",
        command_groups=[
            CommandGroupSpec(
                path=("note",),
                summary="Manage notes",
                description="Manage notes.",
                commands=[
                    _leaf(("create",), "Create a note"),
                    _leaf(("list",), "List notes"),
                ],
                command_groups=[
                    CommandGroupSpec(
                        path=("admin",),
                        summary="Admin note operations",
                        description="Admin note operations.",
                        commands=[
                            _leaf(("prune",), "Prune notes"),
                        ],
                    ),
                ],
            ),
        ],
    )

    payload = app.build_help_payload(["note"])

    assert payload["command_groups"] == [
        {"path": "note admin", "summary": "Admin note operations"},
    ]
    assert payload["commands"] == [
        {"path": "note create", "summary": "Create a note"},
        {"path": "note list", "summary": "List notes"},
    ]

