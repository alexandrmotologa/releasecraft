# ReleaseCraft architecture

ReleaseCraft is structured into modular subsystems: git plumbing, commit parsing, semver calculation, manifest synchronization, changelog synthesis, interactive terminal review, and multi-forge remote release publishing.

```
releasecraft/
├── src/
│   └── releasecraft/
│       ├── __init__.py
│       ├── cli.py                   # Command line interface and entry points
│       ├── config.py                # Configuration loader (.releasecraft.yaml)
│       ├── models.py                # Core domain schemas (Commit, Release, SemVer)
│       ├── git/                     # Git plumbing and commit traversal
│       │   ├── repo_scanner.py      # Identifies latest version tag with ancestry check
│       │   ├── log_walker.py        # Traverses commit DAG between revisions
│       │   └── tagger.py            # Creates signed or annotated git tags
│       ├── manifests/               # Multi-ecosystem manifest version synchronization
│       │   └── updater.py           # pyproject.toml, package.json, Cargo, composer, etc.
│       ├── hooks/                   # Native Git hooks installation and validation
│       │   ├── installer.py         # Installs commit-msg hook into .git/hooks
│       │   └── validator.py         # Validates commit messages against Conventional Commits
│       ├── parser/                  # Conventional Commits extraction
│       │   ├── commit_parser.py     # Parses headers, bodies, scopes, and footers
│       │   ├── semver_calculator.py # Determines major, minor, patch (with zero_semver support)
│       │   └── pr_enricher.py       # Resolves GitHub pull request and issue numbers
│       ├── changelog/               # Markdown changelog generation
│       │   ├── builder.py           # Groups commits into structured sections
│       │   ├── updater.py           # Inserts release notes beneath header/[Unreleased]
│       │   ├── highlights.py        # Synthesizes executive highlights summary block
│       │   └── templates.py         # Markdown formatters
│       ├── publisher/               # Remote release publishing and notifications
│       │   ├── git_pusher.py        # Pushes commits and tags to remote origin with verification
│       │   ├── asset_uploader.py    # Streaming asset upload and SHA256SUMS manifest generation
│       │   ├── webhooks.py          # Discord, Slack, and generic webhook notifications
│       │   ├── github_client.py     # GitHub REST API client
│       │   └── providers/           # Multi-forge release providers
│       │       ├── base.py          # Abstract ReleaseProvider interface
│       │       ├── github.py        # GitHub Releases provider
│       │       ├── gitlab.py        # GitLab Releases provider
│       │       └── gitea.py         # Gitea Releases provider
│       └── tui/                     # Interactive terminal user interface
│           ├── app.py               # Textual application controller
│           ├── screens.py           # Release curation and preview screens
│           └── widgets.py           # Commit checklist and live preview panes
```

## Data flow

1. **Tag resolution**: `RepoScanner` inspects the local git repository tags. It matches tags against standard semantic version patterns (`v1.2.3` or `1.2.3`), verifies branch ancestry (`is_ancestor`), and identifies the highest valid version tag. If the repository has no prior tags, it selects the initial commit as the base.
2. **Commit collection**: `LogWalker` walks the revision history from the base tag to `HEAD`. It extracts commit hashes, author metadata, timestamps, and commit bodies.
3. **Semantic parsing**: `CommitParser` evaluates each commit against Conventional Commits 1.0.0 rules. It extracts the commit type (`feat`, `fix`, `docs`, `perf`, `refactor`), the optional scope, breaking change markers (`!` or `BREAKING CHANGE:`), and footer metadata.
4. **Version calculation**: `SemVerCalculator` evaluates the parsed commits. In standard mode: breaking changes trigger a major bump, new features trigger a minor bump, fixes/perf trigger a patch bump. In Zero-Ver (`--v0`) mode: breaking changes bump minor and features bump patch.
5. **Curation phase**:
   - In automated mode, all qualifying commits are included in the release notes.
   - In interactive mode, the Textual interface allows maintainers to toggle individual commits, reclassify types, edit summaries, and inspect live Markdown previews.
6. **Manifest synchronization**:
   - `ManifestUpdater` locates and atomically updates version declarations in `pyproject.toml`, `package.json`, `Cargo.toml`, `composer.json`, `pubspec.yaml`, `setup.cfg`, `version.go`, and `VERSION`.
7. **Persistence and release**:
   - `ChangelogUpdater` inserts the formatted release entry into `CHANGELOG.md` beneath top headers or `[Unreleased]` sections.
   - `Tagger` creates an annotated local git tag.
   - If enabled, `GitPusher` pushes the commit and tag to the git remote origin.
   - `AssetUploader` streams binary release assets and computes `SHA256SUMS`.
   - `ReleaseProvider` (GitHub, GitLab, or Gitea) publishes the official release notes and attaches binary assets.
   - `WebhookDispatcher` sends announcement payloads to configured Discord, Slack, or generic webhook endpoints.
