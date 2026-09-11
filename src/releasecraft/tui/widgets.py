"""Textual UI widgets for the ReleaseCraft interactive release manager."""

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label, Markdown, Static

from releasecraft.models import BumpType, SemVerInfo


class SemVerHeader(Static):
    """Header bar widget displaying version transition and bump badge."""

    def __init__(
        self,
        current_version: SemVerInfo | None,
        next_version: SemVerInfo,
        bump_type: BumpType,
        *args,
        **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.current_version = current_version
        self.next_version = next_version
        self.bump_type = bump_type

    def render(self) -> str:
        curr_str = f"v{self.current_version}" if self.current_version else "Initial"
        next_str = f"v{self.next_version}"

        bump_color = {
            BumpType.MAJOR: "bold red",
            BumpType.MINOR: "bold green",
            BumpType.PATCH: "bold cyan",
            BumpType.PRERELEASE: "bold yellow",
            BumpType.NONE: "dim",
        }.get(self.bump_type, "white")

        return (
            f" [bold white]ReleaseCraft[/bold white] | Current: [bold]{curr_str}[/bold] "
            f"➔ Proposed: [{bump_color}]{next_str}[/{bump_color}] "
            f"([{bump_color}]{self.bump_type.value.upper()}[/{bump_color}])"
        )


class ChangelogPreviewPane(VerticalScroll):
    """Scrollable Markdown preview pane showing the formatted release notes."""

    def __init__(self, initial_markdown: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.markdown_content = initial_markdown
        self.md_widget = Markdown(initial_markdown)

    def compose(self) -> ComposeResult:
        yield Label("[bold cyan]Live Changelog Preview[/bold cyan]")
        yield self.md_widget

    def update_content(self, new_markdown: str) -> None:
        """Update markdown content dynamically."""
        self.markdown_content = new_markdown
        self.md_widget.update(new_markdown)
