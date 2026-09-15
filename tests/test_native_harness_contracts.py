"""Contracts for the migrated native harness entry point."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_native_setup_and_wizard_contract() -> None:
    """Setup must not hand off to an external task-service-dependent wizard."""
    prompt = ROOT / ".github/prompts/harness-setup.prompt.md"
    wizard = ROOT / ".github/agents/harness-wizard.agent.md"
    for path in (prompt, wizard):
        text = path.read_text(encoding="utf-8")
        assert "archon" not in text.lower(), path
        assert "GitHub issue" in text, path
        assert "resume" in text.lower(), path
        assert "permission" in text.lower(), path
        assert "three" in text.lower(), path
        assert "60 minutes" in text, path
        assert "supervisor" in text.lower(), path
    assert "agent: harness-wizard" in prompt.read_text(encoding="utf-8")
    assert "../prompts/harness-setup.prompt.md" in wizard.read_text(encoding="utf-8")


def test_native_coder_contract() -> None:
    """The coding role must use the native workflow and scoped changes."""
    text = (ROOT / ".github/agents/harness-coder.agent.md").read_text(encoding="utf-8")
    assert "archon" not in text.lower()
    assert "git add ." not in text
    assert "manage_task(" not in text
    assert "../prompts/harness-setup.prompt.md" in text
    assert "independent review" in text
    assert "supervisor" in text


@pytest.mark.parametrize(
    "role", ["wizard", "initializer", "coder", "tester", "reviewer"]
)
def test_core_role_contract(role: str) -> None:
    """Every migrated role must link to setup without obsolete dependencies."""
    path = ROOT / f".github/agents/harness-{role}.agent.md"
    text = path.read_text(encoding="utf-8")
    assert "archon" not in text.lower()
    assert "manage_task(" not in text
    assert "git add ." not in text
    assert "../prompts/harness-setup.prompt.md" in text
    assert "GitHub issue" in text
    assert "supervisor" in text


@pytest.mark.parametrize(
    ("entry", "role"),
    [
        ("init", "initializer"),
        ("next", "coder"),
        ("resume", "wizard"),
        ("status", "coder"),
        ("quick", "wizard"),
    ],
)
def test_entry_prompt_contract(entry: str, role: str) -> None:
    """Migrated entry points must resolve to real native-workflow roles."""
    path = ROOT / f".github/prompts/harness-{entry}.prompt.md"
    text = path.read_text(encoding="utf-8")
    assert "archon" not in text.lower()
    assert "find_tasks(" not in text
    assert "& /harness" not in text
    assert "harness-setup.prompt.md" in text
    assert f"agent: harness-{role}" in text
    assert (ROOT / f".github/agents/harness-{role}.agent.md").is_file()
    assert "GitHub issue" in text
    assert "supervisor" in text


def test_vscode_connection_removed() -> None:
    """The removed task service must not remain configured in VS Code."""
    text = (ROOT / ".vscode/mcp.json").read_text(encoding="utf-8")
    assert '"archon"' not in text.lower()
    assert "localhost:8051" not in text
