"""Git hook installer and uninstaller."""

import os
import stat
from pathlib import Path

HOOK_CONTENT = """#!/bin/sh
# ReleaseCraft commit-msg hook
# Validates commit messages against Conventional Commits 1.0.0

releasecraft hook check-msg "$1"
STATUS=$?

if [ $STATUS -ne 0 ]; then
    echo ""
    echo "[ReleaseCraft] Commit aborted due to formatting error."
    exit $STATUS
fi
"""


class HookInstaller:
    """Installs or removes ReleaseCraft git hooks in a repository."""

    @classmethod
    def get_hooks_dir(cls, repo_root: Path | str) -> Path:
        """Find the .git/hooks directory."""
        git_dir = Path(repo_root) / ".git"
        if git_dir.is_file():
            # Git worktree or submodule pointer
            content = git_dir.read_text(encoding="utf-8").strip()
            if content.startswith("gitdir:"):
                target = content.split(":", 1)[1].strip()
                git_dir = Path(repo_root) / target

        return git_dir / "hooks"

    @classmethod
    def install(cls, repo_root: Path | str) -> Path:
        """Install commit-msg hook into .git/hooks."""
        hooks_dir = cls.get_hooks_dir(repo_root)
        hooks_dir.mkdir(parents=True, exist_ok=True)

        hook_file = hooks_dir / "commit-msg"
        hook_file.write_text(HOOK_CONTENT, encoding="utf-8")

        # Set executable permissions on POSIX
        if os.name != "nt":
            current_stat = os.stat(hook_file)
            os.chmod(hook_file, current_stat.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        return hook_file

    @classmethod
    def uninstall(cls, repo_root: Path | str) -> bool:
        """Remove commit-msg hook if installed by ReleaseCraft."""
        hooks_dir = cls.get_hooks_dir(repo_root)
        hook_file = hooks_dir / "commit-msg"

        if hook_file.is_file():
            content = hook_file.read_text(encoding="utf-8")
            if "ReleaseCraft" in content:
                hook_file.unlink()
                return True

        return False
