"""Integration tests for monorepo path filtering and tag prefixes."""

from pathlib import Path

import git

from releasecraft.git.log_walker import LogWalker
from releasecraft.git.repo_scanner import RepoScanner


def test_monorepo_tag_prefix_and_path_filtering(tmp_path: Path) -> None:
    repo = git.Repo.init(tmp_path)
    with repo.config_writer() as cfg:
        cfg.set_value("user", "name", "Monorepo Dev")
        cfg.set_value("user", "email", "dev@example.com")

    pkg_a = tmp_path / "packages" / "pkg-a"
    pkg_b = tmp_path / "packages" / "pkg-b"
    pkg_a.mkdir(parents=True)
    pkg_b.mkdir(parents=True)

    # Initial commit in pkg-a with tag pkg-a-v1.0.0
    f_a = pkg_a / "index.js"
    f_a.write_text("console.log('a1');", encoding="utf-8")
    repo.index.add([str(f_a)])
    c1 = repo.index.commit("feat(pkg-a): initial pkg-a")
    repo.create_tag("pkg-a-v1.0.0", ref=c1)

    # Initial commit in pkg-b with tag pkg-b-v2.0.0
    f_b = pkg_b / "index.js"
    f_b.write_text("console.log('b1');", encoding="utf-8")
    repo.index.add([str(f_b)])
    c2 = repo.index.commit("feat(pkg-b): initial pkg-b")
    repo.create_tag("pkg-b-v2.0.0", ref=c2)

    # New commit touching only pkg-a
    f_a.write_text("console.log('a2');", encoding="utf-8")
    repo.index.add([str(f_a)])
    repo.index.commit("fix(pkg-a): resolve syntax error")

    # New commit touching only pkg-b
    f_b.write_text("console.log('b2');", encoding="utf-8")
    repo.index.add([str(f_b)])
    repo.index.commit("feat(pkg-b): add streaming feature")

    # Test RepoScanner with prefix
    scanner = RepoScanner(tmp_path)
    tag_a, ver_a = scanner.get_latest_semver_tag(tag_prefix="pkg-a-")
    assert tag_a == "pkg-a-v1.0.0"
    assert ver_a is not None
    assert str(ver_a) == "1.0.0"

    tag_b, ver_b = scanner.get_latest_semver_tag(tag_prefix="pkg-b-")
    assert tag_b == "pkg-b-v2.0.0"
    assert ver_b is not None
    assert str(ver_b) == "2.0.0"

    # Test LogWalker path filtering
    walker = LogWalker(repo)
    commits_pkg_a = walker.get_commits_between(
        base_tag="pkg-a-v1.0.0",
        path_filter="packages/pkg-a",
    )
    assert len(commits_pkg_a) == 1
    assert "fix(pkg-a)" in commits_pkg_a[0].message

    commits_pkg_b = walker.get_commits_between(
        base_tag="pkg-b-v2.0.0",
        path_filter="packages/pkg-b",
    )
    assert len(commits_pkg_b) == 1
    assert "feat(pkg-b)" in commits_pkg_b[0].message
