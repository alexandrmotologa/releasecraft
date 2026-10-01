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
from releasecraft.hooks.installer import HookInstaller
from releasecraft.hooks.validator import CommitMsgValidator
from releasecraft.manifests.updater import ManifestUpdater
from releasecraft.models import BumpType
from releasecraft.parser.commit_parser import CommitParser
from releasecraft.parser.semver_calculator import SemVerCalculator
from releasecraft.publisher.asset_uploader import AssetUploader
from releasecraft.publisher.git_pusher import GitPusher
from releasecraft.publisher.github_client import GitHubClient
from releasecraft.publisher.providers.base import ReleaseProvider
from releasecraft.publisher.providers.gitea import GiteaProvider
from releasecraft.publisher.providers.github import GitHubProvider
from releasecraft.publisher.providers.gitlab import GitLabProvider
from releasecraft.publisher.webhooks import WebhookDispatcher

app = typer.Typer(
    name="releasecraft",
    help="Semantic Git release manager and changelog engine with interactive TUI",
    no_args_is_help=True,
)
hook_app = typer.Typer(
    name="hook",
    help="Git hooks management and commit message validation",
    no_args_is_help=True,
)
app.add_typer(hook_app, name="hook")

console = Console(legacy_windows=False)


@app.command()
def version() -> None:
    """Show ReleaseCraft version and build information."""
    console.print(f"[bold cyan]ReleaseCraft[/bold cyan] v{__version__}")


@hook_app.command("install")
def hook_install(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
) -> None:
    """Install the commit-msg git hook to validate conventional commits."""
    hook_file = HookInstaller.install(repo_path)
    console.print(f"[bold green]✓ Installed commit-msg hook:[/bold green] {hook_file}")


@hook_app.command("uninstall")
def hook_uninstall(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
) -> None:
    """Remove the ReleaseCraft commit-msg hook."""
    removed = HookInstaller.uninstall(repo_path)
    if removed:
        console.print("[bold green]✓ Successfully removed commit-msg hook.[/bold green]")
    else:
        console.print("[yellow]No ReleaseCraft hook was found to remove.[/yellow]")


@hook_app.command("check-msg")
def hook_check_msg(
    msg_file: Annotated[
        Path,
        typer.Argument(
            help="File containing commit message to validate", exists=True, dir_okay=False
        ),
    ],
) -> None:
    """Validate a commit message file against Conventional Commits 1.0.0."""
    is_valid, err = CommitMsgValidator.validate_file(msg_file)
    if not is_valid:
        console.print(f"[bold red]Commit rejected:[/bold red]\n{err}")
        raise typer.Exit(code=1)
    console.print("[green]✓ Commit message follows Conventional Commits format.[/green]")


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
    path_filter: Annotated[
        str | None, typer.Option("--path", help="Filter commits by file or folder path")
    ] = None,
    scope_filter: Annotated[
        str | None, typer.Option("--scope", help="Filter commits by conventional scope")
    ] = None,
    tag_prefix: Annotated[
        str, typer.Option("--tag-prefix", help="Prefix for version tags (e.g. 'cli-')")
    ] = "",
    v0: Annotated[
        bool, typer.Option("--v0/--no-v0", help="Enable 0.x Zero-Ver SemVer rules")
    ] = False,
    highlights: Annotated[
        bool,
        typer.Option("--highlights/--no-highlights", help="Include executive highlights block"),
    ] = False,
) -> None:
    """Preview next semantic version and release notes without making changes."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    effective_prefix = tag_prefix if tag_prefix != "" else config.tag_prefix
    last_tag, current_ver = scanner.get_latest_semver_tag(tag_prefix=effective_prefix)

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(
        base_tag=last_tag,
        reverse=True,
        path_filter=path_filter,
    )

    if not raw_commits:
        console.print("[yellow]No new commits found since last release tag.[/yellow]")
        raise typer.Exit(code=0)

    parsed_commits = CommitParser.parse_many(raw_commits)
    if scope_filter:
        parsed_commits = [c for c in parsed_commits if c.scope == scope_filter]

    is_zero_semver = v0 or config.zero_semver
    next_ver, bump_type = SemVerCalculator.calculate_next_version(
        current_version=current_ver,
        commits=parsed_commits,
        zero_semver=is_zero_semver,
    )

    builder = ChangelogBuilder(config=config)
    markdown, sections = builder.build_markdown(
        version=next_ver,
        commits=parsed_commits,
        prev_version=current_ver,
        include_hidden=include_all,
        include_highlights=highlights,
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

    curr_display = f"{tag_prefix}v{current_ver}" if current_ver else "None (Initial)"
    panel_text = (
        f"[bold]Current Version:[/bold] {curr_display}\n"
        f"[bold]Next Version:[/bold] [bold green]{tag_prefix}v{next_ver}[/bold green] "
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
    tag_prefix: Annotated[str, typer.Option("--tag-prefix", help="Tag prefix filter")] = "",
) -> None:
    """Validate unreleased commits against Conventional Commits specifications."""
    scanner = RepoScanner(repo_path)
    last_tag, _ = scanner.get_latest_semver_tag(tag_prefix=tag_prefix)

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
    path_filter: Annotated[
        str | None, typer.Option("--path", help="Filter commits by directory path")
    ] = None,
    highlights: Annotated[
        bool, typer.Option("--highlights/--no-highlights", help="Include highlights block")
    ] = False,
    tag_prefix: Annotated[
        str, typer.Option("--tag-prefix", help="Prefix for version tags (e.g. 'cli-')")
    ] = "",
    v0: Annotated[
        bool, typer.Option("--v0/--no-v0", help="Enable 0.x Zero-Ver SemVer rules")
    ] = False,
) -> None:
    """Generate or update CHANGELOG.md without tagging or publishing."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    effective_prefix = tag_prefix if tag_prefix != "" else config.tag_prefix
    last_tag, current_ver = scanner.get_latest_semver_tag(tag_prefix=effective_prefix)

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(
        base_tag=last_tag,
        reverse=True,
        path_filter=path_filter,
    )

    if not raw_commits:
        console.print("[yellow]No commits to document in changelog.[/yellow]")
        return

    parsed_commits = CommitParser.parse_many(raw_commits)
    if version_override:
        from releasecraft.models import SemVerInfo

        target_ver = SemVerInfo.from_string(version_override)
    else:
        is_zero_semver = v0 or config.zero_semver
        target_ver, _ = SemVerCalculator.calculate_next_version(
            current_ver,
            parsed_commits,
            zero_semver=is_zero_semver,
        )

    builder = ChangelogBuilder(config=config)
    markdown, _ = builder.build_markdown(
        version=target_ver,
        commits=parsed_commits,
        prev_version=current_ver,
        include_highlights=highlights,
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
        bool,
        typer.Option(
            "--publish/--no-publish", help="Publish release to forge (GitHub/GitLab/Gitea)"
        ),
    ] = True,
    provider: Annotated[
        str, typer.Option("--provider", help="Git forge provider: auto, github, gitlab, gitea")
    ] = "auto",
    v0: Annotated[
        bool, typer.Option("--v0/--no-v0", help="Enable 0.x Zero-Ver SemVer rules")
    ] = False,
    push_remote: Annotated[
        bool, typer.Option("--push/--no-push", help="Push commit and tag to git remote")
    ] = True,
    remote_name: Annotated[str, typer.Option("--remote", help="Git remote name")] = "origin",
    path_filter: Annotated[
        str | None, typer.Option("--path", help="Filter commits by directory path (monorepo)")
    ] = None,
    scope_filter: Annotated[
        str | None, typer.Option("--scope", help="Filter commits by conventional scope")
    ] = None,
    tag_prefix: Annotated[
        str, typer.Option("--tag-prefix", help="Tag prefix (e.g. 'cli-' or 'pkg-')")
    ] = "",
    assets: Annotated[
        list[str] | None,
        typer.Option("--assets", "-a", help="Asset glob pattern to attach to release"),
    ] = None,
    generate_checksums: Annotated[
        bool,
        typer.Option(
            "--generate-checksums/--no-checksums", help="Generate SHA256SUMS file for assets"
        ),
    ] = True,
    bump_manifests: Annotated[
        bool,
        typer.Option(
            "--bump-manifests/--no-bump-manifests",
            help="Update version in pyproject.toml/package.json",
        ),
    ] = True,
    highlights: Annotated[
        bool,
        typer.Option("--highlights/--no-highlights", help="Include executive highlights summary"),
    ] = False,
    webhook: Annotated[
        str | None, typer.Option("--webhook", help="Webhook URL to notify on release completion")
    ] = None,
    webhook_type: Annotated[
        str, typer.Option("--webhook-type", help="Webhook payload format: discord, slack, generic")
    ] = "generic",
) -> None:
    """Analyze commits, bump semantic version, update changelog, tag, and publish release."""
    scanner = RepoScanner(repo_path)
    config = ReleaseCraftConfig.load(scanner.git_root)
    effective_prefix = tag_prefix if tag_prefix != "" else config.tag_prefix
    last_tag, current_ver = scanner.get_latest_semver_tag(tag_prefix=effective_prefix)

    walker = LogWalker(scanner.repo)
    raw_commits = walker.get_commits_between(
        base_tag=last_tag,
        reverse=True,
        path_filter=path_filter,
    )

    if not raw_commits:
        console.print("[yellow]No new commits to release.[/yellow]")
        raise typer.Exit(code=0)

    parsed_commits = CommitParser.parse_many(raw_commits)
    if scope_filter:
        parsed_commits = [c for c in parsed_commits if c.scope == scope_filter]

    builder = ChangelogBuilder(config=config)
    is_zero_semver = v0 or config.zero_semver

    if interactive:
        from releasecraft.tui.app import ReleaseCraftApp

        tui_app = ReleaseCraftApp(
            current_version=current_ver,
            commits=parsed_commits,
            builder=builder,
        )
        tui_app.run()
        if not tui_app.confirmed:
            console.print("[yellow]Release process cancelled by user in TUI.[/yellow]")
            raise typer.Exit(code=0)

        next_ver = tui_app.next_version
        bump_type = tui_app.bump_type
        release_markdown = tui_app.current_markdown
    else:
        next_ver, bump_type = SemVerCalculator.calculate_next_version(
            current_version=current_ver,
            commits=parsed_commits,
            bump_override=bump,
            prerelease_token=prerelease,
            zero_semver=is_zero_semver,
        )
        release_markdown, _ = builder.build_markdown(
            version=next_ver,
            commits=parsed_commits,
            prev_version=current_ver,
            include_highlights=highlights,
        )

    tag_template = (
        f"{effective_prefix}{config.tag_format}" if effective_prefix else config.tag_format
    )
    tag_name = tag_template.format(version=str(next_ver))
    console.print(
        f"[bold green]Prepared Release:[/bold green] {tag_name} ({bump_type.value.upper()})"
    )

    # Resolve assets
    effective_assets = assets if assets is not None else (config.release.assets or None)
    effective_checksums = generate_checksums and config.release.generate_checksums
    resolved_assets: list[Path] = []
    if effective_assets:
        resolved_assets = AssetUploader.resolve_asset_paths(
            effective_assets, base_dir=scanner.git_root
        )
        if effective_checksums and resolved_assets:
            checksums_path = scanner.git_root / "SHA256SUMS"
            AssetUploader.generate_checksums_file(resolved_assets, checksums_path)
            if checksums_path not in resolved_assets:
                resolved_assets.append(checksums_path)

    if dry_run:
        console.print(
            "[bold yellow][DRY RUN MODE][/bold yellow] The following actions would occur:"
        )
        console.print(f"1. Update {config.changelog_path} with release notes")
        if bump_manifests:
            detected_m = ManifestUpdater.detect_manifests(scanner.git_root)
            console.print(f"2. Bump versions to {next_ver} in: {[m.name for m in detected_m]}")
        console.print(f"3. git commit -m 'chore(release): {tag_name}'")
        console.print(f"4. git tag -a {tag_name} -m 'Release {tag_name}'")
        if push_remote:
            console.print(f"5. git push {remote_name} {scanner.get_current_branch_name()} --tags")
        if publish_github:
            console.print(
                f"6. Forge release '{tag_name}' created with {len(resolved_assets)} attached assets"
            )
        if webhook:
            console.print(f"7. Dispatch release notification to {webhook_type} webhook")
        console.print("\n[dim]Generated Changelog Notes:[/dim]")
        console.print(release_markdown)
        return

    # 1. Update project manifests
    modified_files: list[Path] = []
    if bump_manifests:
        bumped = ManifestUpdater.update_all(scanner.git_root, str(next_ver))
        for b in bumped:
            console.print(f"[green]✓ Bumped manifest: {b.name} ➔ {next_ver}[/green]")
            modified_files.append(b)

    # 2. Update CHANGELOG.md
    changelog_file = scanner.git_root / config.changelog_path
    ChangelogUpdater.update_file(changelog_file, release_markdown)
    console.print(f"[green]✓ Updated {config.changelog_path}[/green]")
    modified_files.append(changelog_file)

    # 3. Commit staged files
    scanner.repo.index.add([str(f) for f in modified_files])
    commit_msg = f"chore(release): {tag_name}"
    scanner.repo.index.commit(commit_msg)
    console.print(f"[green]✓ Committed: '{commit_msg}'[/green]")

    # 4. Create Git Tag
    tagger = GitTagger(scanner.repo)
    tagger.create_tag(tag_name=tag_name, message=f"Release {tag_name}", sign=config.sign_tag)
    console.print(f"[green]✓ Created tag: {tag_name}[/green]")

    # 5. Push to Remote
    if push_remote:
        pusher = GitPusher(scanner.repo, remote_name=remote_name)
        actions = pusher.push(tag_name=tag_name, branch_name=scanner.get_current_branch_name())
        for a in actions:
            console.print(f"[green]✓ {a}[/green]")

    # 6. Publish to Forge (GitHub, GitLab, Gitea)
    published_url = ""
    if publish_github:
        remote_url = None
        if remote_name in [r.name for r in scanner.repo.remotes]:
            remote_url = list(scanner.repo.remotes[remote_name].urls)[0]

        target_provider = provider.lower() if provider != "auto" else config.provider.lower()
        if target_provider == "auto" and remote_url:
            if "gitlab" in remote_url.lower():
                target_provider = "gitlab"
            elif "gitea" in remote_url.lower() or "forgejo" in remote_url.lower():
                target_provider = "gitea"
            else:
                target_provider = "github"
        elif target_provider == "auto":
            target_provider = "github"

        repo_slug = config.github_repo or (
            GitHubClient.extract_repo_from_remote_url(remote_url) if remote_url else None
        )
        current_branch = scanner.get_current_branch_name()

        if repo_slug:
            try:
                forge_client: ReleaseProvider
                if target_provider == "gitlab":
                    forge_client = GitLabProvider(project_id=repo_slug)
                elif target_provider == "gitea":
                    forge_client = GiteaProvider(repo=repo_slug)
                else:
                    forge_client = GitHubProvider(repo=repo_slug)

                release_info = forge_client.create_release(
                    tag_name=tag_name,
                    name=tag_name,
                    body=release_markdown,
                    target_commitish=current_branch,
                    prerelease=bool(next_ver.prerelease),
                    assets=resolved_assets,
                )
                published_url = release_info.get("html_url") or release_info.get("tag_name", "")
                console.print(
                    f"[bold green]✓ {target_provider.capitalize()} release published:[/bold green] {published_url or tag_name}"
                )
            except Exception as ex:
                console.print(
                    f"[yellow]Warning: Could not publish {target_provider} release: {ex}[/yellow]"
                )
        else:
            console.print(
                f"[yellow]Notice: No repository found to publish release notes to {target_provider}.[/yellow]"
            )

    # 7. Dispatch Webhooks
    webhooks_to_dispatch: list[tuple[str, str]] = []
    if webhook:
        webhooks_to_dispatch.append((webhook, webhook_type))
    elif config.webhooks:
        for wh in config.webhooks:
            webhooks_to_dispatch.append((wh.url, wh.type))

    for wh_url, wh_type in webhooks_to_dispatch:
        try:
            WebhookDispatcher.dispatch(
                webhook_url=wh_url,
                webhook_type=wh_type,
                title=f"Release {tag_name}",
                tag_name=tag_name,
                release_url=published_url,
                changelog_snippet=release_markdown,
            )
            console.print(f"[green]✓ Webhook notification dispatched ({wh_type})[/green]")
        except Exception as ex:
            console.print(f"[yellow]Warning: Webhook dispatch failed: {ex}[/yellow]")

    console.print(f"[bold green]Release {tag_name} completed successfully![/bold green]")


SAMPLE_CONFIG = """# ReleaseCraft configuration file (.releasecraft.yaml)
# Documentation: https://github.com/alexandrmotologa/releasecraft

# Tag format template. Default: "v{version}"
tag_format: "v{version}"

# Optional tag prefix (e.g. for monorepos: "cli-")
tag_prefix: ""

# Target changelog file path. Default: "CHANGELOG.md"
changelog_path: "CHANGELOG.md"

# Git remote name. Default: "origin"
remote: "origin"

# Automatically bump version declarations in manifests
bump_manifests: true

# Enable 0.x Zero-Ver rules (breaking bumps minor, feat bumps patch)
zero_semver: false

# Forge provider: auto, github, gitlab, gitea
provider: "auto"

# Conventional commit section definitions
sections:
  - type: "breaking"
    title: "Breaking Changes"
    emoji: "⚠️"
    hidden: false
  - type: "feat"
    title: "Features"
    emoji: "🚀"
    hidden: false
  - type: "fix"
    title: "Bug Fixes"
    emoji: "🐛"
    hidden: false
  - type: "perf"
    title: "Performance Improvements"
    emoji: "⚡"
    hidden: false
  - type: "security"
    title: "Security"
    emoji: "🔒"
    hidden: false
  - type: "refactor"
    title: "Code Refactoring"
    emoji: "🔄"
    hidden: true
  - type: "docs"
    title: "Documentation"
    emoji: "📚"
    hidden: true
  - type: "chore"
    title: "Maintenance"
    emoji: "🔧"
    hidden: true

# Release options
release:
  sign_tag: false
  create_draft: false
  generate_checksums: true
  assets: []

# Webhook announcements
# webhooks:
#   - url: "https://discord.com/api/webhooks/..."
#     type: "discord"
"""


@app.command("init")
def init_config(
    repo_path: Annotated[
        Path,
        typer.Argument(help="Path to git repository", exists=True, file_okay=False, dir_okay=True),
    ] = Path("."),
    force: Annotated[
        bool, typer.Option("--force", "-f", help="Overwrite existing configuration file")
    ] = False,
    install_hook: Annotated[
        bool, typer.Option("--hook/--no-hook", help="Install git commit-msg hook")
    ] = True,
) -> None:
    """Initialize a .releasecraft.yaml configuration file and optional commit-msg hook."""
    config_file = repo_path / ".releasecraft.yaml"
    if config_file.exists() and not force:
        console.print(f"[yellow]Configuration file already exists: {config_file}[/yellow]")
        console.print("Use [bold]--force[/bold] to overwrite.")
    else:
        config_file.write_text(SAMPLE_CONFIG, encoding="utf-8")
        console.print(f"[bold green]✓ Created configuration file:[/bold green] {config_file}")

    if install_hook:
        try:
            hook_file = HookInstaller.install(repo_path)
            console.print(f"[bold green]✓ Installed commit-msg hook:[/bold green] {hook_file}")
        except Exception as ex:
            console.print(f"[yellow]Notice: Could not install git hook: {ex}[/yellow]")
