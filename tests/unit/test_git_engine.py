"""Unit tests for Git engine modules: RepoScanner, LogWalker, and GitTagger."""

from pathlib import Path

import git
import pytest

from releasecraft.git.log_walker import LogWalker
from releasecraft.git.repo_scanner import RepoScanner
from releasecraft.git.tagger import GitTagger


@pytest.fixture
def synthetic_repo(tmp_path: Path) -> git.Repo:
    """Fixture providing a temporary git repository with configured user identity."""
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test Committer")
        config.set_value("user", "email", "committer@example.com")
    return repo


def test_repo_scanner_no_tags(synthetic_repo: git.Repo, tmp_path: Path) -> None:
    """Verify RepoScanner behavior on a fresh repository without tags."""
    # Create initial commit
    file1 = tmp_path / "README.md"
    file1.write_text("# Initial", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    synthetic_repo.index.commit("chore: initial commit")

    scanner = RepoScanner(tmp_path)
    tag, version = scanner.get_latest_semver_tag()
    assert tag is None
    assert version is None

    root = scanner.get_root_commit()
    assert root.hexsha == synthetic_repo.head.commit.hexsha


def test_repo_scanner_with_semver_tags(synthetic_repo: git.Repo, tmp_path: Path) -> None:
    """Verify RepoScanner correctly detects and sorts semantic tags."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("v1", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    commit1 = synthetic_repo.index.commit("feat: first commit")
    synthetic_repo.create_tag("v0.1.0", ref=commit1, message="Version 0.1.0")

    file1.write_text("v2", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    commit2 = synthetic_repo.index.commit("feat: second commit")
    synthetic_repo.create_tag("v1.0.0", ref=commit2, message="Version 1.0.0")

    file1.write_text("v3", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    commit3 = synthetic_repo.index.commit("feat: third commit")
    synthetic_repo.create_tag("v1.2.0", ref=commit3, message="Version 1.2.0")

    # Add non-semver tag
    synthetic_repo.create_tag("test-build-tag", ref=commit3)

    scanner = RepoScanner(tmp_path)
    tag, version = scanner.get_latest_semver_tag()
    assert tag == "v1.2.0"
    assert version is not None
    assert version.major == 1
    assert version.minor == 2
    assert version.patch == 0


def test_repo_scanner_ignores_unreachable_branch_tags(
    synthetic_repo: git.Repo, tmp_path: Path
) -> None:
    """Verify RepoScanner ignores tags created on unmerged feature branches."""
    # Commit on main with v1.0.0
    f = tmp_path / "main.txt"
    f.write_text("main v1", encoding="utf-8")
    synthetic_repo.index.add([str(f)])
    c1 = synthetic_repo.index.commit("chore: commit on main")
    synthetic_repo.create_tag("v1.0.0", ref=c1)

    # Create and checkout feature branch
    feat_branch = synthetic_repo.create_head("feature/v2")
    feat_branch.checkout()

    f.write_text("feature v2", encoding="utf-8")
    synthetic_repo.index.add([str(f)])
    c2 = synthetic_repo.index.commit("feat!: breaking change on feature branch")
    synthetic_repo.create_tag("v2.0.0", ref=c2)

    # Switch back to main
    synthetic_repo.heads.master.checkout() if "master" in synthetic_repo.heads else synthetic_repo.heads[
        0
    ].checkout()

    scanner = RepoScanner(tmp_path)
    tag, version = scanner.get_latest_semver_tag()

    # The highest tag on main should be v1.0.0, NOT the unmerged v2.0.0
    assert tag == "v1.0.0"
    assert version is not None
    assert version.major == 1
    assert version.minor == 0


def test_log_walker_fetches_range(synthetic_repo: git.Repo, tmp_path: Path) -> None:
    """Verify LogWalker correctly retrieves commits between a base tag and HEAD."""
    file1 = tmp_path / "app.py"
    file1.write_text("print('v1')", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    c1 = synthetic_repo.index.commit("feat: initial version")
    synthetic_repo.create_tag("v1.0.0", ref=c1)

    file1.write_text("print('v2')", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    synthetic_repo.index.commit("fix: resolve bug in app")

    file1.write_text("print('v3')", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    synthetic_repo.index.commit("feat: add new feature")

    walker = LogWalker(synthetic_repo)
    commits = walker.get_commits_between(base_tag="v1.0.0", reverse=True)

    assert len(commits) == 2
    assert commits[0].message == "fix: resolve bug in app"
    assert commits[1].message == "feat: add new feature"
    assert commits[0].author_name == "Test Committer"


def test_log_walker_all_commits_when_no_tag(synthetic_repo: git.Repo, tmp_path: Path) -> None:
    """Verify LogWalker retrieves all commits when base_tag is None."""
    file1 = tmp_path / "file.txt"
    for i in range(3):
        file1.write_text(f"line {i}", encoding="utf-8")
        synthetic_repo.index.add([str(file1)])
        synthetic_repo.index.commit(f"feat: commit number {i}")

    walker = LogWalker(synthetic_repo)
    commits = walker.get_commits_between(base_tag=None, reverse=True)
    assert len(commits) == 3
    assert commits[0].message == "feat: commit number 0"
    assert commits[2].message == "feat: commit number 2"


def test_git_tagger_operations(synthetic_repo: git.Repo, tmp_path: Path) -> None:
    """Verify GitTagger creates, verifies, and deletes tags."""
    file1 = tmp_path / "setup.py"
    file1.write_text("# setup", encoding="utf-8")
    synthetic_repo.index.add([str(file1)])
    synthetic_repo.index.commit("chore: init setup")

    tagger = GitTagger(synthetic_repo)
    assert not tagger.tag_exists("v2.0.0")

    tag_ref = tagger.create_tag("v2.0.0", message="Release 2.0.0")
    assert tag_ref.name == "v2.0.0"
    assert tagger.tag_exists("v2.0.0")

    # Creating duplicate tag should raise error
    with pytest.raises(ValueError, match="already exists"):
        tagger.create_tag("v2.0.0", message="Duplicate")

    # Delete tag
    tagger.delete_tag("v2.0.0")
    assert not tagger.tag_exists("v2.0.0")
