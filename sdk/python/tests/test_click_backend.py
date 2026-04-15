import json

from aclip import AclipApp, ArgumentSpec, CommandGroupSpec, CommandSpec


def test_click_backend_parses_choices_multiple_and_envvar(monkeypatch, capsys):
    monkeypatch.setenv("ACLIP_FILTER_STORE", ".env-store.json")

    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI for click backend coverage.",
        command_groups=[
            CommandGroupSpec(
                path=("filter",),
                summary="Filter notes",
                description="Run note filtering operations.",
            )
        ],
        commands=[
            CommandSpec(
                path=("filter", "run"),
                summary="Run filters",
                description="Run one filter command.",
                arguments=[
                    ArgumentSpec(
                        name="mode",
                        kind="string",
                        flag="--mode",
                        choices=["fast", "safe"],
                        required=True,
                        description="Execution mode.",
                    ),
                    ArgumentSpec(
                        name="tag",
                        kind="string",
                        flag="--tag",
                        multiple=True,
                        description="Repeatable tag filter.",
                    ),
                    ArgumentSpec(
                        name="store",
                        kind="string",
                        flag="--store",
                        env_var="ACLIP_FILTER_STORE",
                        description="Store path.",
                    ),
                ],
                examples=[
                    "demo filter run --mode fast --tag a --tag b",
                ],
                output_schema={"type": "object"},
                output_summary="Returns the parsed filter arguments.",
                handler=lambda arguments: arguments,
            )
        ],
    )

    exit_code = app.run(["filter", "run", "--mode", "fast", "--tag", "a", "--tag", "b"])

    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["mode"] == "fast"
    assert payload["data"]["tag"] == ["a", "b"]
    assert payload["data"]["store"] == ".env-store.json"


def test_command_detail_exposes_choices_multiple_envvar_and_usage_shape():
    app = AclipApp(
        name="demo",
        version="0.1.0",
        summary="Demo CLI",
        description="Demo CLI for click backend coverage.",
        command_groups=[
            CommandGroupSpec(
                path=("filter",),
                summary="Filter notes",
                description="Run note filtering operations.",
            )
        ],
        commands=[
            CommandSpec(
                path=("filter", "run"),
                summary="Run filters",
                description="Run one filter command.",
                arguments=[
                    ArgumentSpec(
                        name="mode",
                        kind="string",
                        flag="--mode",
                        choices=["fast", "safe"],
                        required=True,
                        description="Execution mode.",
                    ),
                    ArgumentSpec(
                        name="tag",
                        kind="string",
                        flag="--tag",
                        multiple=True,
                        description="Repeatable tag filter.",
                    ),
                    ArgumentSpec(
                        name="store",
                        kind="string",
                        flag="--store",
                        env_var="ACLIP_FILTER_STORE",
                        description="Store path.",
                    ),
                ],
                examples=[
                    "demo filter run --mode fast --tag a --tag b",
                ],
                output_schema={"type": "object"},
                output_summary="Returns the parsed filter arguments.",
                handler=lambda arguments: arguments,
            )
        ],
    )

    detail = app.build_command_detail(["filter", "run"])

    assert detail["arguments"][0]["choices"] == ["fast", "safe"]
    assert detail["arguments"][1]["multiple"] is True
    assert detail["arguments"][2]["envVar"] == "ACLIP_FILTER_STORE"
    assert detail["usage"] == (
        "demo filter run --mode <string> [--tag <string>]... [--store <string>]"
    )

