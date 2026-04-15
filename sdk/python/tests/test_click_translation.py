import click

from aclip import ArgumentSpec
from aclip.click_backend import translate_argument_spec


def test_argument_spec_no_longer_exposes_parser_translation():
    argument = ArgumentSpec(name="title", kind="string", description="Title")

    assert not hasattr(argument, "argparse_parts")


def test_translate_argument_spec_preserves_core_click_shapes():
    string_parameter = translate_argument_spec(
        ArgumentSpec(name="title", kind="string", description="Title", required=True)
    )
    integer_parameter = translate_argument_spec(
        ArgumentSpec(name="count", kind="integer", description="Count", default=3)
    )
    boolean_parameter = translate_argument_spec(
        ArgumentSpec(name="verbose", kind="boolean", description="Verbose")
    )
    positional_parameter = translate_argument_spec(
        ArgumentSpec(
            name="session_id",
            kind="string",
            description="Session identifier.",
            positional=True,
            required=True,
        )
    )
    rich_parameter = translate_argument_spec(
        ArgumentSpec(
            name="mode",
            kind="string",
            description="Execution mode.",
            flag="--mode",
            choices=["fast", "safe"],
            multiple=True,
            env_var="ACLIP_MODE",
        )
    )

    assert isinstance(string_parameter, click.Option)
    assert string_parameter.opts == ["--title"]
    assert string_parameter.required is True
    assert string_parameter.type is click.STRING

    assert isinstance(integer_parameter, click.Option)
    assert integer_parameter.opts == ["--count"]
    assert integer_parameter.type is click.INT
    assert integer_parameter.default == 3

    assert isinstance(boolean_parameter, click.Option)
    assert boolean_parameter.opts == ["--verbose"]
    assert boolean_parameter.is_flag is True
    assert boolean_parameter.default is False

    assert isinstance(positional_parameter, click.Argument)
    assert positional_parameter.name == "session_id"
    assert positional_parameter.required is True
    assert positional_parameter.type is click.STRING

    assert isinstance(rich_parameter, click.Option)
    assert rich_parameter.opts == ["--mode"]
    assert isinstance(rich_parameter.type, click.Choice)
    assert list(rich_parameter.type.choices) == ["fast", "safe"]
    assert rich_parameter.multiple is True
    assert rich_parameter.envvar == "ACLIP_MODE"

