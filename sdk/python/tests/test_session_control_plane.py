from aclip import (
    AclipApp,
    SessionCommandConfig,
    build_session_control_plane,
)


def _config(
    *,
    summary: str,
    description: str,
    example: str,
    output_summary: str,
    payload: dict,
) -> SessionCommandConfig:
    return SessionCommandConfig(
        summary=summary,
        description=description,
        examples=[example],
        output_summary=output_summary,
        handler=lambda _args, result=payload: result,
    )


def test_session_control_plane_builds_reserved_group_and_baseline_commands():
    control_plane = build_session_control_plane(
        group_summary="Manage sessions",
        group_description="Create, inspect, list, and close resumable sessions.",
        create=_config(
            summary="Create a session",
            description="Create a new author-owned session resource.",
            example="demo session create",
            output_summary="Returns a JSON object whose `session` field contains the created session.",
            payload={"session": {"id": "sess-1", "status": "active"}},
        ),
        list_=_config(
            summary="List sessions",
            description="List visible sessions.",
            example="demo session list",
            output_summary="Returns a JSON object whose `sessions` field contains visible sessions.",
            payload={"sessions": []},
        ),
        get=_config(
            summary="Get a session",
            description="Inspect one session.",
            example="demo session get sess-1",
            output_summary="Returns a JSON object whose `session` field contains the requested session.",
            payload={"session": {"id": "sess-1", "status": "active"}},
        ),
        close=_config(
            summary="Close a session",
            description="Close one session.",
            example="demo session close sess-1",
            output_summary="Returns a JSON object whose `session` field contains the closed session.",
            payload={"session": {"id": "sess-1", "status": "closed"}},
        ),
    )

    assert control_plane.command_group.path == ("session",)
    assert control_plane.command_group.summary == "Manage sessions"
    assert [command.path for command in control_plane.commands] == [
        ("session", "create"),
        ("session", "list"),
        ("session", "get"),
        ("session", "close"),
    ]

    command_map = {command.command_name(): command for command in control_plane.commands}
    assert command_map["session create"].arguments == []
    assert command_map["session list"].arguments == []
    assert command_map["session get"].arguments[0].name == "session_id"
    assert command_map["session get"].arguments[0].positional is True
    assert command_map["session close"].arguments[0].name == "session_id"


def test_session_control_plane_adds_optional_commands_only_when_configured():
    control_plane = build_session_control_plane(
        group_summary="Manage sessions",
        group_description="Create, inspect, list, and close resumable sessions.",
        create=_config(
            summary="Create a session",
            description="Create a session resource.",
            example="demo session create",
            output_summary="Returns a created session.",
            payload={"session": {"id": "sess-1"}},
        ),
        list_=_config(
            summary="List sessions",
            description="List sessions.",
            example="demo session list",
            output_summary="Returns visible sessions.",
            payload={"sessions": []},
        ),
        get=_config(
            summary="Get a session",
            description="Inspect one session.",
            example="demo session get sess-1",
            output_summary="Returns one session.",
            payload={"session": {"id": "sess-1"}},
        ),
        close=_config(
            summary="Close a session",
            description="Close one session.",
            example="demo session close sess-1",
            output_summary="Returns a closed session.",
            payload={"session": {"id": "sess-1"}},
        ),
        delete=_config(
            summary="Delete a session",
            description="Delete one session.",
            example="demo session delete sess-1",
            output_summary="Returns a deleted session.",
            payload={"session": {"id": "sess-1"}},
        ),
        touch=_config(
            summary="Touch a session",
            description="Refresh one session.",
            example="demo session touch sess-1",
            output_summary="Returns a touched session.",
            payload={"session": {"id": "sess-1"}},
        ),
        exec_=_config(
            summary="Execute in a session",
            description="Run one author-defined operation through a session context.",
            example="demo session exec sess-1 sync",
            output_summary="Returns the author-defined execution result.",
            payload={"result": {"ok": True}},
        ),
    )

    command_map = {command.command_name(): command for command in control_plane.commands}

    assert list(command_map) == [
        "session create",
        "session list",
        "session get",
        "session close",
        "session delete",
        "session touch",
        "session exec",
    ]
    assert command_map["session delete"].arguments[0].name == "session_id"
    assert command_map["session touch"].arguments[0].name == "session_id"
    assert [argument.name for argument in command_map["session exec"].arguments] == [
        "session_id",
        "operation",
    ]


def test_session_control_plane_output_integrates_with_aclip_app_help():
    control_plane = build_session_control_plane(
        group_summary="Manage sessions",
        group_description="Create, inspect, list, and close resumable sessions.",
        create=_config(
            summary="Create a session",
            description="Create a new author-owned session resource.",
            example="demo session create",
            output_summary="Returns a JSON object whose `session` field contains the created session.",
            payload={"session": {"id": "sess-1", "status": "active"}},
        ),
        list_=_config(
            summary="List sessions",
            description="List visible sessions.",
            example="demo session list",
            output_summary="Returns a JSON object whose `sessions` field contains visible sessions.",
            payload={"sessions": []},
        ),
        get=_config(
            summary="Get a session",
            description="Inspect one session.",
            example="demo session get sess-1",
            output_summary="Returns a JSON object whose `session` field contains the requested session.",
            payload={"session": {"id": "sess-1", "status": "active"}},
        ),
        close=_config(
            summary="Close a session",
            description="Close one session.",
            example="demo session close sess-1",
            output_summary="Returns a JSON object whose `session` field contains the closed session.",
            payload={"session": {"id": "sess-1", "status": "closed"}},
        ),
    )

    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI with optional session support.",
        command_groups=[control_plane.command_group],
        commands=control_plane.commands,
    )

    root_payload = app.build_help_payload()
    group_payload = app.build_help_payload(["session"])
    command_payload = app.build_command_detail(["session", "get"])

    assert root_payload["command_groups"] == [{"path": "session", "summary": "Manage sessions"}]
    assert group_payload["commands"] == [
        {"path": "session create", "summary": "Create a session"},
        {"path": "session list", "summary": "List sessions"},
        {"path": "session get", "summary": "Get a session"},
        {"path": "session close", "summary": "Close a session"},
    ]
    assert command_payload["usage"] == "demo session get <session_id:string>"

