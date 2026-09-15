"""Tests for GitHub App registration security boundaries."""

import pytest
from register_app import manifest, valid_callback


def test_manifest_limits_permissions() -> None:
    result = manifest("http://127.0.0.1:8765")
    assert result["public"] is False
    assert result["default_permissions"] == {
        "administration": "write",
        "actions": "read",
    }
    assert result["default_events"] == []
    hook = result["hook_attributes"]
    assert isinstance(hook, dict)
    assert hook["active"] is False
    assert result["redirect_url"] == "http://127.0.0.1:8765/callback"


def test_valid_callback() -> None:
    assert (
        valid_callback("state=session&code=abcdefghij123", "session") == "abcdefghij123"
    )


@pytest.mark.parametrize(
    "query",
    [
        "",
        "state=session",
        "code=abcdefghij123",
        "state=wrong&code=abcdefghij123",
        "state=session&state=session&code=abcdefghij123",
        "state=session&code=abcdefghij123&code=abcdefghij123",
        "state=session&code=",
        "state=session&code=short",
        "state=session&code=../../abcdefghij",
    ],
)
def test_rejects_invalid_callback(query: str) -> None:
    with pytest.raises(ValueError):
        valid_callback(query, "session")
