# Contributing to ReleaseCraft

Thank you for your interest in contributing to ReleaseCraft.

## Development setup

1. Clone the repository:
   ```bash
   git clone https://github.com/alexandrmotologa/releasecraft.git
   cd releasecraft
   ```

2. Create and activate a virtual environment:
   ```bash
   uv venv
   # On Linux/macOS:
   source .venv/bin/activate
   # On Windows:
   .venv\Scripts\activate
   ```

3. Install editable dependencies:
   ```bash
   uv pip install -e ".[dev]"
   ```

## Workflow and standards

- **Conventional commits**: Every commit must follow Conventional Commits 1.0.0 (`feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`, `chore:`). Breaking changes must include `!` or a `BREAKING CHANGE:` footer.
- **Linting and formatting**: Code must pass Ruff checks:
  ```bash
  uv run ruff check src tests
  uv run ruff format --check src tests
  ```
- **Testing**: Run pytest before opening pull requests:
  ```bash
  uv run pytest
  ```

## Pull requests

1. Create a descriptive feature branch from `main`.
2. Keep changes focused on a single concern.
3. Include tests covering new functionality or bug fixes.
4. Ensure all CI checks pass.
