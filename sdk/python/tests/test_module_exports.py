import importlib
import sys


def test_root_import_does_not_eagerly_import_packaging():
    sys.modules.pop("aclip", None)
    sys.modules.pop("aclip.packaging", None)

    module = importlib.import_module("aclip")

    assert "aclip.packaging" not in sys.modules
    assert module.AclipApp.__name__ == "AclipApp"
    assert "aclip.packaging" not in sys.modules

    _ = module.build_cli

    assert "aclip.packaging" in sys.modules
