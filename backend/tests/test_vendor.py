import hashlib
from pathlib import Path


VENDOR_ROOT = (
    Path(__file__).resolve().parents[1]
    / "memory_court"
    / "vendor"
    / "sonuv_guard"
)

EXPECTED_SHA256 = {
    "__init__.py": "b458f841ccd172b8dc9a8b7b7dbcf60399ca8733f1f21de07213d133591119f7",
    "ast_eval.py": "1d00e02171421e93ec460b9f1f2dc9f14ea4538e3eb9e22eba0de7bd0fa580b4",
    "creator_validator.py": "1d54693698d7f5e3be5e6d1ddc3e05f6179d79d38a26fe7e092b46cc6b162685",
    "engine.py": "2536826822f6c56de0612fba6bdb262cd852ae76ca0ce92fa2c0f02502400bfe",
    "guard.py": "cb4071cc0223ed42f8c1ccea0d6e21a51e4f1c3cdcf8b71bb74269ef316b2f8f",
    "models.py": "f63619640dddf8346da7639db6ee9daa8f92d3e69cf93a8fa15142e293929689",
    "sanitize.py": "2f3f104d79f8055b5638259748433cde05c03c6598b56fb45649854df6155cc2",
    "store.py": "c48f07faed5ca199e05dfab179c4becae3f174cd865b77ec05ff2230307c70d5",
}


def test_vendored_guard_is_exact_upstream_runtime_snapshot() -> None:
    actual = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in VENDOR_ROOT.glob("*.py")
    }

    assert actual == EXPECTED_SHA256
