"""Git remote push manager."""

import git


class GitPusher:
    """Handles pushing commits and tags to remote repositories."""

    def __init__(self, repo: git.Repo, remote_name: str = "origin") -> None:
        self.repo = repo
        self.remote_name = remote_name

    def verify_remote(self) -> bool:
        """Check if the configured remote exists in the repository."""
        return self.remote_name in [r.name for r in self.repo.remotes]

    def get_remote_url(self) -> str | None:
        """Get the URL of the configured remote."""
        if self.verify_remote():
            return list(self.repo.remotes[self.remote_name].urls)[0]
        return None

    def push(
        self,
        tag_name: str | None = None,
        branch_name: str | None = None,
        dry_run: bool = False,
    ) -> list[str]:
        """Push branch and tag to remote.

        Args:
            tag_name: Optional tag name to push.
            branch_name: Optional branch name to push (defaults to current branch).
            dry_run: If True, simulates push actions without executing them.

        Returns:
            List of human-readable action log messages.
        """
        actions = []
        if not self.verify_remote():
            raise ValueError(f"Git remote '{self.remote_name}' not found.")

        target_branch = branch_name or self.repo.active_branch.name
        actions.append(f"Pushing branch '{target_branch}' to '{self.remote_name}'")

        if tag_name:
            actions.append(f"Pushing tag '{tag_name}' to '{self.remote_name}'")

        if dry_run:
            return actions

        remote = self.repo.remotes[self.remote_name]

        # Push branch
        remote.push(refspec=f"{target_branch}:{target_branch}")

        # Push tag if specified
        if tag_name:
            remote.push(refspec=f"refs/tags/{tag_name}:refs/tags/{tag_name}")

        return actions
