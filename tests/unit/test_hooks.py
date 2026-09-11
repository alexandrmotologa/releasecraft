"""Unit tests for Git hooks validator and installer."""

from pathlib import Path

import git

from releasecraft.hooks.installer import HookInstaller
from releasecraft.hooks.validator import CommitMsgValidator


def test_validator_valid_messages() -> None:
    valid_msgs = [
        "feat: add oauth2 provider",
        "fix(parser): handle empty lines in footers",
        "feat(api)!: break backward compatibility",
        "refactor: clean up git plumbing",
        "docs(readme): add installation guide",
        "Merge branch 'feature/awesome' into main",
    ]
    for msg in valid_msgs:
        is_valid, err = CommitMsgValidator.validate_message(msg)
        assert is_valid, f"Expected '{msg}' to be valid, got: {err}"
        assert err == ""


def test_validator_invalid_messages() -> None:
    invalid_cases = [
        ("fixed the bug", "Invalid commit header format"),
        ("update readme", "Invalid commit header format"),
        ("foo(api): unknown type", "Unknown commit type 'foo'"),
        ("feat:", "Invalid commit header format"),
        ("", "Commit message is empty."),
    ]
    for msg, expected_snippet in invalid_cases:
        is_valid, err = CommitMsgValidator.validate_message(msg)
        assert not is_valid
        assert expected_snippet in err


def test_validator_strips_git_comments() -> None:
    msg_with_comments = (
        "feat(ui): add dark theme\n\n"
        "# Please enter the commit message for your changes.\n"
        "# Lines starting with '#' will be ignored.\n"
    )
    is_valid, err = CommitMsgValidator.validate_message(msg_with_comments)
    assert is_valid
    assert err == ""


def test_hook_installer_and_uninstaller(tmp_path: Path) -> None:
    git.Repo.init(tmp_path)
    hook_path = HookInstaller.install(tmp_path)

    assert hook_path.is_file()
    assert "ReleaseCraft" in hook_path.read_text(encoding="utf-8")

    # Uninstall
    uninstalled = HookInstaller.uninstall(tmp_path)
    assert uninstalled is True
    assert not hook_path.is_file()
