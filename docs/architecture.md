# ReleaseCraft architecture

ReleaseCraft is structured into six decoupled modules: git plumbing, commit parsing, semver calculation, changelog synthesis, interactive terminal review, and remote release publishing.

```
releasecraft/
├── src/
│   └── releasecraft/
│       ├── __init__.py
│       ├── cli.py                   # Command line interface and entry points
│       ├── config.py                # Configuration loader (.releasecraft.yaml)
│       ├── models.py                # Core domain schemas (Commit, Release, SemVer)
│       ├── git/                     # Git plumbing and commit traversal
│       │   ├── repo_scanner.py      # Identifies latest version tag or root commit
│       │   ├── log_walker.py        # Traverses commit DAG between revisions
│       │   └── tagger.py            # Creates signed or annotated git tags
│       ├── parser/                  # Conventional Commits extraction
│       │   ├── commit_parser.py     # Parses headers, bodies, and footers
│       │   ├── semver_calculator.py # Determines major, minor, or patch increment
│       │   └── pr_enricher.py       # Resolves GitHub pull request and issue numbers
│       ├── changelog/               # Markdown changelog generation
│       │   ├── builder.py           # Groups commits into structured sections
│       │   ├── updater.py           # Prepends release notes into CHANGELOG.md
│       │   └── templates.py         # Markdown formatters
│       ├── publisher/               # Remote git and release operations
│       │   ├── github_client.py     # GitHub REST API client for releases
│       │   └── git_pusher.py        # Pushes commits and tags to remote origin
│       └── tui/                     # Interactive terminal user interface
│           ├── app.py               # Textual application controller
│           ├── screens.py           # Release curation and preview screens
│           └── widgets.py           # Commit checklist and live preview panes
```

## Data flow

1. **Tag resolution**: `RepoScanner` inspects the local git repository tags. It matches tags against standard semantic version patterns (`v1.2.3` or `1.2.3`) and identifies the highest version tag. If the repository has no prior tags, it selects the initial commit as the base.
2. **Commit collection**: `LogWalker` walks the revision history from the base tag to `HEAD`. It extracts commit hashes, author metadata, timestamps, and commit bodies.
3. **Semantic parsing**: `CommitParser` evaluates each commit against Conventional Commits 1.0.0 rules. It extracts the commit type (`feat`, `fix`, `docs`, `perf`, `refactor`), the optional scope, breaking change markers (`!` or `BREAKING CHANGE:`), and footer metadata.
4. **Version calculation**: `SemVerCalculator` evaluates the parsed commits. Breaking changes trigger a major bump. New features trigger a minor bump. Fixes and performance improvements trigger a patch bump.
5. **Curation phase**:
   - In automated mode, all qualifying commits are included in the release notes.
   - In interactive mode, the Textual interface allows maintainers to toggle individual commits, exclude internal chore commits, or edit entry summaries.
6. **Persistence and release**:
   - `ChangelogUpdater` inserts the formatted release entry into `CHANGELOG.md` directly beneath the top-level heading.
   - `Tagger` creates an annotated local git tag.
   - If enabled, `GitPusher` pushes the commit and tag to origin.
   - `GitHubClient` sends a POST request to the GitHub REST API to create the official release.
