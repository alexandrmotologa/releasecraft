"""Git log walker to traverse commit history between revisions."""

from datetime import UTC, datetime

import git

from releasecraft.models import RawCommit


class LogWalker:
    """Traverses git commit history and converts commits into domain representations."""

    def __init__(self, repo: git.Repo) -> None:
        self.repo = repo

    def get_commits_between(
        self,
        base_tag: str | None = None,
        head_ref: str = "HEAD",
        reverse: bool = True,
    ) -> list[RawCommit]:
        """Fetch commits between base_tag and head_ref.

        Args:
            base_tag: Name of the previous tag or commit hash. If None, fetches all commits to head_ref.
            head_ref: Target head reference (default: HEAD).
            reverse: If True, returns oldest commits first (chronological order).
                     If False, returns newest commits first.

        Returns:
            List of RawCommit instances.
        """
        if base_tag:
            rev_range = f"{base_tag}..{head_ref}"
            try:
                git_commits = list(self.repo.iter_commits(rev_range))
            except git.GitCommandError as err:
                # Fallback if rev_range syntax fails
                raise ValueError(f"Failed to resolve commit range {rev_range}") from err
        else:
            # All commits up to head_ref
            git_commits = list(self.repo.iter_commits(head_ref))

        raw_commits: list[RawCommit] = []
        for c in git_commits:
            # Commit timestamp in UTC
            dt = datetime.fromtimestamp(c.committed_date, tz=UTC)
            raw = RawCommit(
                hash=c.hexsha,
                short_hash=c.hexsha[:7],
                author_name=c.author.name or "Unknown",
                author_email=c.author.email or "unknown@example.com",
                timestamp=dt,
                message=c.message.strip(),
                parent_hashes=[p.hexsha for p in c.parents],
            )
            raw_commits.append(raw)

        if reverse:
            raw_commits.reverse()

        return raw_commits
