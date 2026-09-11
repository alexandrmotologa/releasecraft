"""Command-line interface for ReleaseCraft."""

import json
import sys
from pathlib import Path
from typing import Annotated

# Ensure UTF-8 output on Windows consoles to support emojis and symbols
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from releasecraft import __version__
from releasecraft.changelog.builder import ChangelogBuilder
from releasecraft.changelog.updater import ChangelogUpdater
from releasecraft.config import ReleaseCraftConfig
from releasecraft.git.log_walker import LogWalker
from releasecraft.git.repo_scanner import RepoScanner
from releasecraft.git.tagger import GitTagger
from releasecraft.models import BumpType
from releasecraft.parser.commit_parser import CommitParser
from releasecraft.parser.semver_calculator import SemVerCalculator
from releasecraft.publisher.git_pusher import GitPusher
from releasecraft.publisher.github_client import GitHubClient

app = typer.Typer(
    name="releasecraft",
    help="Semantic Git release manager and changelog engine with interactive TUI",
    no_args_is_help=True,
)
console = Console(legacy_windows=False)


@app.command()
def version() -> None:
    """Show ReleaseCraft version and build information."""
    console.print(f"[bold cyan]ReleaseCraft[/bold cyan] v{__version__}")


@app.command()
def preview(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
    as_json: Annotated[bool, typer.Option("--json", help="Output results as JSON")] = False,
    include_all: Annotated[
        bool, typer.Option("--include-all", help="Include all commit types in release notes")
    ] = False,
) -> None:
    """Preview next semantic version and release notes without making changes."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    last_tag, current_ver = scanner.get_latest_semver_tag()

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(base_tag=last_tag, reverse=True)

    if not raw_commits:
        console.print("[yellow]No new commits found since last release tag.[/yellow]")
        raise typer.Exit(code=0)

    parsed_commits = CommitParser.parse_many(raw_commits)
    next_ver, bump_type = SemVerCalculator.calculate_next_version(
        current_version=current_ver,
        commits=parsed_commits,
    )

    builder = ChangelogBuilder(config=config)
    markdown, sections = builder.build_markdown(
        version=next_ver,
        commits=parsed_commits,
        prev_version=current_ver,
        include_hidden=include_all,
    )

    if as_json:
        data = {
            "current_version": str(current_ver) if current_ver else None,
            "next_version": str(next_ver),
            "bump_type": bump_type.value,
            "commit_count": len(parsed_commits),
            "changelog": markdown,
        }
        typer.echo(json.dumps(data, indent=2))
        return

    curr_display = f"v{current_ver}" if current_ver else "None (Initial)"
    panel_text = (
        f"[bold]Current Version:[/bold] {curr_display}\n"
        f"[bold]Next Version:[/bold] [bold green]v{next_ver}[/bold green] "
        f"([cyan]{bump_type.value.upper()}[/cyan] bump across {len(parsed_commits)} commits)\n"
    )
    console.print(Panel(panel_text, title="ReleaseCraft Preview", border_style="cyan"))
    console.print(markdown)


@app.command()
def check(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
) -> None:
    """Validate unreleased commits against Conventional Commits specifications."""
    scanner = RepoScanner(repo_path)
    last_tag, _ = scanner.get_latest_semver_tag()

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(base_tag=last_tag, reverse=True)

    if not raw_commits:
        console.print("[green]No unreleased commits to check.[/green]")
        return

    table = Table(title=f"Commit Convention Check ({len(raw_commits)} commits)")
    table.add_column("Hash", style="dim")
    table.add_column("Type", style="bold")
    table.add_column("Scope")
    table.add_column("Breaking", justify="center")
    table.add_column("Subject")

    has_breaking = False
    for raw in raw_commits:
        parsed = CommitParser.parse(raw)
        breaking_mark = "⚠️ YES" if parsed.is_breaking else "No"
        if parsed.is_breaking:
            has_breaking = True

        type_style = "green" if parsed.type in ("feat", "fix", "perf") else "white"
        table.add_row(
            raw.short_hash,
            f"[{type_style}]{parsed.type}[/{type_style}]",
            parsed.scope or "-",
            breaking_mark,
            parsed.subject,
        )

    console.print(table)
    if has_breaking:
        console.print(
            "[yellow]Note: Breaking changes detected. This will trigger a MAJOR bump.[/yellow]"
        )


@app.command()
def changelog(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
    output: Annotated[
        Path, typer.Option("--output", "-o", help="Target changelog file path")
    ] = Path("CHANGELOG.md"),
    version_override: Annotated[
        str | None, typer.Option("--version", help="Explicit version for the changelog block")
    ] = None,
) -> None:
    """Generate or update CHANGELOG.md without tagging or publishing."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    last_tag, current_ver = scanner.get_latest_semver_tag()

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(base_tag=last_tag, reverse=True)

    if not raw_commits:
        console.print("[yellow]No commits to document in changelog.[/yellow]")
        return

    parsed_commits = CommitParser.parse_many(raw_commits)
    if version_override:
        from releasecraft.models import SemVerInfo

        target_ver = SemVerInfo.from_string(version_override)
    else:
        target_ver, _ = SemVerCalculator.calculate_next_version(current_ver, parsed_commits)

    builder = ChangelogBuilder(config=config)
    markdown, _ = builder.build_markdown(
        version=target_ver,
        commits=parsed_commits,
        prev_version=current_ver,
    )

    target_file = scanner.git_root / output
    ChangelogUpdater.update_file(target_file, markdown)
    console.print(f"[bold green]Updated {target_file} for version v{target_ver}[/bold green]")


@app.command()
def release(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
    interactive: Annotated[
        bool,
        typer.Option(
            "--interactive/--no-interactive", "-i", help="Launch interactive TUI to curate release"
        ),
    ] = False,
    dry_run: Annotated[
        bool, typer.Option("--dry-run", help="Simulate release without modifying git or remote")
    ] = False,
    bump: Annotated[
        BumpType | None, typer.Option("--bump", help="Force specific version bump type")
    ] = None,
    prerelease: Annotated[
        str | None, typer.Option("--prerelease", help="Pre-release identifier (e.g. rc, beta)")
    ] = None,
    publish_github: Annotated[
        bool, typer.Option("--publish/--no-publish", help="Publish release to GitHub")
    ] = True,
    push_remote: Annotated[
        bool, typer.Option("--push/--no-push", help="Push commit and tag to git remote")
    ] = True,
    remote_name: Annotated[str, typer.Option("--remote", help="Git remote name")] = "origin",
) -> None:
    """Analyze commits, bump semantic version, update changelog, tag, and publish release."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    last_tag, current_ver = scanner.get_latest_semver_tag()

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(base_tag=last_tag, reverse=True)

    if not raw_commits:
        console.print("[yellow]No new commits to release.[/yellow]")
        raise typer.Exit(code=0)

    parsed_commits = CommitParser.parse_many(raw_commits)
    builder = ChangelogBuilder(config=config)

    if interactive:
        from releasecraft.tui.app import ReleaseCraftApp

        app = ReleaseCraftApp(
            current_version=current_ver,
            commits=parsed_commits,
            builder=builder,
        )
        app.run()
        if not app.confirmed:
            console.print("[yellow]Release process cancelled by user in TUI.[/yellow]")
            raise typer.Exit(code=0)

        next_ver = app.next_version
        bump_type = app.bump_type
        release_markdown = app.current_markdown
    else:
        next_ver, bump_type = SemVerCalculator.calculate_next_version(
            current_version=current_ver,
            commits=parsed_commits,
            bump_override=bump,
            prerelease_token=prerelease,
        )
        release_markdown, _ = builder.build_markdown(
            version=next_ver,
            commits=parsed_commits,
            prev_version=current_ver,
        )

    tag_name = config.tag_format.format(version=str(next_ver))
    console.print(
        f"[bold green]Prepared Release:[/bold green] {tag_name} ({bump_type.value.upper()})"
    )

    if dry_run:
        console.print(
            "[bold yellow][DRY RUN MODE][/bold yellow] The following actions would occur:"
        )
        console.print(f"1. Update {config.changelog_path} with release notes")
        console.print(f"2. git commit -m 'chore(release): {tag_name}'")
        console.print(f"3. git tag -a {tag_name} -m 'Release {tag_name}'")
        if push_remote:
            console.print(f"4. git push {remote_name} {scanner.get_current_branch_name()} --tags")
        if publish_github:
            console.print(f"5. GitHub release '{tag_name}' created via REST API")
        console.print("\n[dim]Generated Changelog Notes:[/dim]")
        console.print(release_markdown)
        return

    # 1. Update CHANGELOG.md
    changelog_file = scanner.git_root / config.changelog_path
    ChangelogUpdater.update_file(changelog_file, release_markdown)
    console.print(f"[green]✓ Updated {config.changelog_path}[/green]")

    # 2. Commit CHANGELOG.md
    scanner.repo.index.add([str(changelog_file)])
    commit_msg = f"chore(release): {tag_name}"
    scanner.repo.index.commit(commit_msg)
    console.print(f"[green]✓ Committed: '{commit_msg}'[/green]")

    # 3. Create Git Tag
    tagger = GitTagger(scanner.repo)
    tagger.create_tag(tag_name=tag_name, message=f"Release {tag_name}", sign=config.sign_tag)
    console.print(f"[green]✓ Created tag: {tag_name}[/green]")

    # 4. Push to Remote
    if push_remote:
        pusher = GitPusher(scanner.repo, remote_name=remote_name)
        actions = pusher.push(tag_name=tag_name, branch_name=scanner.get_current_branch_name())
        for a in actions:
            console.print(f"[green]✓ {a}[/green]")

    # 5. Publish to GitHub
    if publish_github:
        remote_url = None
        if remote_name in [r.name for r in scanner.repo.remotes]:
            remote_url = list(scanner.repo.remotes[remote_name].urls)[0]

        gh_repo = config.github_repo or (
            GitHubClient.extract_repo_from_remote_url(remote_url) if remote_url else None
        )
        if gh_repo:
            try:
                gh_client = GitHubClient(repo=gh_repo)
                release_info = gh_client.create_release(
                    tag_name=tag_name,
                    name=tag_name,
                    body=release_markdown,
                    prerelease=bool(next_ver.prerelease),
                )
                html_url = release_info.get("html_url", "")
                console.print(f"[bold green]✓ GitHub release published:[/bold green] {html_url}")
            except Exception as ex:
                console.print(f"[yellow]Warning: Could not publish GitHub release: {ex}[/yellow]")
        else:
            console.print(
                "[yellow]Notice: No GitHub repository found to publish release notes.[/yellow]"
            )

    console.print(f"[bold green]Release {tag_name} completed successfully![/bold green]")
