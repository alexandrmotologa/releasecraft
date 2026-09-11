"""Git repository scanner for tag resolution and revision roots."""

import re
from pathlib import Path

import git
import semver

from releasecraft.models import SemVerInfo

SEMVER_REGEX = re.compile(
    r"^v?(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+(?P<buildmetadata>[0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
)


class RepoScanner:
    """Scans git repository for semantic tags and commit boundaries."""

    def __init__(self, repo_path: Path | str | None = None) -> None:
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        try:
            self.repo = git.Repo(self.repo_path, search_parent_directories=True)
        except git.InvalidGitRepositoryError as err:
            raise ValueError(f"Path is not a valid git repository: {self.repo_path}") from err

    @property
    def git_root(self) -> Path:
        """Absolute root path of the git repository."""
        return Path(self.repo.working_tree_dir)

    def get_latest_semver_tag(self, tag_prefix: str = "") -> tuple[str | None, SemVerInfo | None]:
        """Find the highest semantic version tag in the repository matching optional prefix.

        Args:
            tag_prefix: Optional prefix filter (e.g. 'cli-' or 'pkg-').

        Returns:
            Tuple of (tag_name, SemVerInfo). If no semantic tags exist, returns (None, None).
        """
        valid_tags: list[tuple[semver.Version, str]] = []

        for tag in self.repo.tags:
            tag_name = tag.name
            if tag_prefix and not tag_name.startswith(tag_prefix):
                continue

            target_version_str = tag_name[len(tag_prefix) :] if tag_prefix else tag_name
            match = SEMVER_REGEX.match(target_version_str)
            if match:
                clean_ver = target_version_str.lstrip("v").lstrip("V")
                try:
                    parsed = semver.Version.parse(clean_ver)
                    valid_tags.append((parsed, tag_name))
                except ValueError:
                    continue

        if not valid_tags:
            return None, None

        # Sort tags by semver.Version
        valid_tags.sort(key=lambda item: item[0])
        highest_version, tag_name = valid_tags[-1]

        semver_info = SemVerInfo(
            major=highest_version.major,
            minor=highest_version.minor,
            patch=highest_version.patch,
            prerelease=highest_version.prerelease,
            build=highest_version.build,
        )
        return tag_name, semver_info

    def get_root_commit(self) -> git.Commit:
        """Find the initial root commit of the current branch."""
        # Find commits with zero parents
        roots = []
        for commit in self.repo.iter_commits():
            if not commit.parents:
                roots.append(commit)

        if not roots:
            raise ValueError("Repository contains no commits.")

        # Return the oldest root commit
        return roots[-1]

    def get_head_commit(self) -> git.Commit:
        """Retrieve the HEAD commit."""
        return self.repo.head.commit

    def get_current_branch_name(self) -> str:
        """Get active branch name or detached HEAD indicator."""
        try:
            return self.repo.active_branch.name
        except TypeError:
            return "HEAD"
