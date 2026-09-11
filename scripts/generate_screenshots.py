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
            "feat(manifest): add multi-ecosystem version synchronizer for pyproject, package.json, and cargo",
            "feat",
            "manifest",
            False,
            False,
            "Adds automated parsing and synchronized bumping for pyproject.toml, package.json, Cargo.toml, and __init__.py files with atomic rollback protection.",
        ),
        (
            "1c2d3e4",
            "feat(hooks): provide native git commit-msg hook installer and validator",
            "feat",
            "hooks",
            False,
            False,
            "Enforces Conventional Commits 1.0.0 directly during git commit workflows with informative colorized diagnostic feedback.",
        ),
        (
            "5f6a7b8",
            "feat(publisher): dispatch webhooks to discord, slack, and custom endpoints",
            "feat",
            "publisher",
            False,
            False,
            "Notifies developer and user channels upon release creation with rich embeds and changelog summaries.",
        ),
        (
            "9d0e1f2",
            "feat(publisher): upload release assets and generate sha256 checksums",
            "feat",
            "publisher",
            False,
            False,
            "Automatically computes SHA256SUMS file and attaches distribution wheels, binaries, and tarballs to GitHub, GitLab, and Gitea releases.",
        ),
        (
            "3b4c5d6",
            "perf(scanner): cache tag lookup and tree diffing for massive monorepos",
            "perf",
            "scanner",
            False,
            False,
            "Reduces git log traversal latency by 68% when calculating paths and tag ranges in repositories with over 50,000 commits.",
        ),
        (
            "8e9f0a1",
            "fix(tui): resolve keybinding clash between search filter and quick shortcuts",
            "fix",
            "tui",
            False,
            False,
            "Ensures search input correctly claims focus on slash key while retaining p, e, m shortcuts when selection list is active.",
        ),
        (
            "4a5b6c7",
            "docs(readme): enrich architectural guide and visual workflows",
            "docs",
            "readme",
            False,
            False,
            "Documents full CLI commands, TUI interactive flows, and multi-forge CI/CD automation templates.",
        ),
        (
            "2e3f4a5",
            "feat(api)!: transition to async release publisher pipeline",
            "feat",
            "api",
            True,
            True,
            "BREAKING CHANGE: Synchronous publisher functions are deprecated in favor of asynchronous provider handlers.",
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
        f"[dim]Forge Provider: GitHub (alexandrmotologa/releasecraft) | Manifests: pyproject.toml[/dim]"
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
