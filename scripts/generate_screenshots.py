"""Generate real application screenshots (SVG) for ReleaseCraft documentation."""

import asyncio
import io
import sys
from datetime import UTC, datetime
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.models import BumpType, ParsedCommit, RawCommit, SemVerInfo
from releasecraft.tui.app import ReleaseCraftApp


def get_demo_commits() -> list[ParsedCommit]:
    """Provide realistic ReleaseCraft commit history for screenshot capture."""
    sample_data = [
        (
            "7a8b9c0",
            "feat(manifest): support composer, pubspec, setup.cfg, and version.go manifests",
            "feat",
            "manifest",
            False,
            False,
            "Adds automated parsing and synchronized bumping for composer.json, pubspec.yaml, setup.cfg, version.go, pyproject.toml, package.json, and Cargo.toml.",
        ),
        (
            "1c2d3e4",
            "feat(cli): add init command for configuration scaffolding and git hook setup",
            "feat",
            "cli",
            False,
            False,
            "Scaffolds default .releasecraft.yaml and installs native commit-msg hooks with interactive or non-interactive flags.",
        ),
        (
            "5f6a7b8",
            "feat(semver): support zero-semver v0 mode for initial development iterations",
            "feat",
            "semver",
            False,
            False,
            "Enables --v0 mode where breaking changes bump minor (0.x -> 0.y) and features bump patch (0.x.y -> 0.x.z).",
        ),
        (
            "9d0e1f2",
            "feat(publisher): multi-forge release publishing for GitHub, GitLab, and Gitea",
            "feat",
            "publisher",
            False,
            False,
            "Seamlessly detects remote forges and credentials to publish releases and upload binary assets with streaming I/O.",
        ),
        (
            "3b4c5d6",
            "perf(scanner): verify branch ancestry to filter unreachable semver tags",
            "perf",
            "scanner",
            False,
            False,
            "Excludes tags from unmerged parallel branches using git ancestry verification before computing version boundaries.",
        ),
        (
            "8e9f0a1",
            "fix(tui): reset breaking flag on reclassification and guard UI lifecycle",
            "fix",
            "tui",
            False,
            False,
            "Ensures commit is_breaking state is properly cleaned up when changing types and guards preview mount lifecycle.",
        ),
        (
            "4a5b6c7",
            "fix(changelog): prevent duplicate breaking feats and preserve unreleased block",
            "fix",
            "changelog",
            False,
            False,
            "Positions release entries accurately beneath [Unreleased] headers and keeps breaking commits exclusive to Breaking Changes.",
        ),
        (
            "2e3f4a5",
            "feat(api)!: transition to unified multi-forge release provider pipeline",
            "feat",
            "api",
            True,
            True,
            "BREAKING CHANGE: Synchronous publisher functions are deprecated in favor of unified ReleaseProvider handlers.",
        ),
    ]

    commits = []
    now = datetime.now(UTC)
    for short_hash, raw_msg, commit_type, scope, is_breaking, body in [
        (s[0], s[1], s[2], s[3], s[4], s[6]) for s in sample_data
    ]:
        raw = RawCommit(
            hash=f"{short_hash}1234567890abcdef1234567890abcdef",
            short_hash=short_hash,
            author_name="Alexander Motologa",
            author_email="alex@releasecraft.dev",
            timestamp=now,
            message=f"{raw_msg}\n\n{body}",
        )
        parsed = ParsedCommit(
            raw=raw,
            type=commit_type,
            scope=scope,
            is_breaking=is_breaking,
            subject=raw_msg.split(": ", 1)[1] if ": " in raw_msg else raw_msg,
            body=body,
            breaking_description="Synchronous publisher functions are deprecated in favor of asynchronous provider handlers."
            if is_breaking
            else None,
        )
        commits.append(parsed)
    return commits


async def capture_tui_screenshot(commits: list[ParsedCommit], output_path: Path) -> None:
    """Run ReleaseCraftApp headless and export an SVG screenshot."""
    current_ver = SemVerInfo(major=1, minor=1, patch=0)
    builder = ChangelogBuilder()

    app = ReleaseCraftApp(
        current_version=current_ver,
        commits=commits,
        builder=builder,
        initial_bump_type=BumpType.MAJOR,
    )

    async with app.run_test(size=(124, 38)) as pilot:
        # Allow components to mount and render preview
        await pilot.pause(0.2)
        svg_content = app.export_screenshot()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(svg_content, encoding="utf-8")
        print(f"[OK] Generated TUI screenshot SVG: {output_path}")


def capture_cli_preview_screenshot(commits: list[ParsedCommit], output_path: Path) -> None:
    """Capture rich terminal output for releasecraft preview command."""
    buf = io.StringIO()
    console = Console(
        file=buf, record=True, width=110, color_system="truecolor", legacy_windows=False
    )

    current_ver = SemVerInfo(major=1, minor=1, patch=0)
    next_ver = SemVerInfo(major=2, minor=0, patch=0)

    panel_text = (
        f"[bold]Current Version:[/bold] v{current_ver}\n"
        f"[bold]Next Version:[/bold] [bold green]v{next_ver}[/bold green] "
        f"([bold cyan]MAJOR[/bold cyan] bump across {len(commits)} unreleased commits)\n"
        f"[dim]Forge Provider: GitHub (alexandrmotologa/releasecraft) | Manifests: pyproject.toml, package.json, composer.json[/dim]"
    )
    console.print(Panel(panel_text, title="ReleaseCraft Release Preview", border_style="cyan"))

    builder = ChangelogBuilder(github_repo="alexandrmotologa/releasecraft")
    markdown_content, _ = builder.build_markdown(
        version=next_ver,
        commits=commits,
        prev_version=current_ver,
        include_highlights=True,
    )

    console.print(Markdown(markdown_content))
    console.save_svg(str(output_path), title="ReleaseCraft Preview")
    print(f"[OK] Generated CLI preview SVG: {output_path}")


def capture_cli_check_screenshot(commits: list[ParsedCommit], output_path: Path) -> None:
    """Capture rich terminal output for releasecraft check command."""
    buf = io.StringIO()
    console = Console(
        file=buf, record=True, width=110, color_system="truecolor", legacy_windows=False
    )

    table = Table(
        title=f"ReleaseCraft Convention Check ({len(commits)} commits inspected)",
        border_style="bright_blue",
        header_style="bold cyan",
    )
    table.add_column("Hash", style="dim", width=9)
    table.add_column("Type", style="bold", width=8)
    table.add_column("Scope", style="magenta", width=12)
    table.add_column("Breaking", justify="center", width=10)
    table.add_column("Subject", style="white")

    for c in commits:
        breaking_badge = (
            "[bold red]⚠️ YES[/bold red]" if c.is_breaking else "[dim green]No[/dim green]"
        )
        type_color = (
            "green"
            if c.type in ("feat", "fix", "perf")
            else "yellow"
            if c.type == "docs"
            else "white"
        )
        table.add_row(
            c.raw.short_hash,
            f"[{type_color}]{c.type}[/{type_color}]",
            c.scope or "-",
            breaking_badge,
            c.subject,
        )

    console.print(table)
    console.print(
        Panel(
            "[bold yellow]Notice:[/bold yellow] Breaking change detected in commit [dim]2e3f4a5[/dim] (scope: [magenta]api[/magenta]).\n"
            "Calculated Semantic Versioning rule: [bold red]MAJOR[/bold red] bump required (v1.1.0 -> [bold green]v2.0.0[/bold green]).",
            border_style="yellow",
        )
    )
    console.save_svg(str(output_path), title="ReleaseCraft Commit Convention Check")
    print(f"[OK] Generated CLI check SVG: {output_path}")


async def main():
    commits = get_demo_commits()
    images_dir = Path("docs/images")
    images_dir.mkdir(parents=True, exist_ok=True)

    await capture_tui_screenshot(commits, images_dir / "tui_screenshot.svg")
    capture_cli_preview_screenshot(commits, images_dir / "cli_preview.svg")
    capture_cli_check_screenshot(commits, images_dir / "cli_check.svg")


if __name__ == "__main__":
    asyncio.run(main())
