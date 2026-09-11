"""Modal screens for inline editing and reclassification in ReleaseCraft TUI."""

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList
from textual.widgets.option_list import Option


class EditCommitModal(ModalScreen[str | None]):
    """Modal dialog allowing maintainers to edit a commit description inline."""

    CSS = """
    EditCommitModal {
        align: center middle;
        background: rgba(15, 23, 42, 0.75);
    }

    #dialog {
        width: 60;
        height: auto;
        background: #1e293b;
        border: solid #38bdf8;
        padding: 1 2;
    }

    #dialog Label {
        margin-bottom: 1;
        color: #f8fafc;
        text-style: bold;
    }

    #dialog Input {
        margin-bottom: 1;
        background: #0f172a;
        color: #f8fafc;
        border: solid #3b82f6;
    }
    """

    def __init__(self, initial_text: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.initial_text = initial_text

    def compose(self) -> ComposeResult:
        with Vertical(id="dialog"):
            yield Label("Edit Release Note Subject:")
            self.input = Input(value=self.initial_text, id="commit-input")
            yield self.input
            yield Label("[dim]Press Enter to confirm, Esc to cancel[/dim]")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def key_escape(self) -> None:
        self.dismiss(None)


class ReclassifyModal(ModalScreen[str | None]):
    """Modal dialog for reassigning a commit to a different conventional type."""

    CSS = """
    ReclassifyModal {
        align: center middle;
        background: rgba(15, 23, 42, 0.75);
    }

    #reclassify-dialog {
        width: 50;
        height: auto;
        background: #1e293b;
        border: solid #6366f1;
        padding: 1 2;
    }

    #reclassify-dialog Label {
        margin-bottom: 1;
        color: #f8fafc;
        text-style: bold;
    }

    OptionList {
        height: 10;
        background: #0f172a;
    }
    """

    TYPES = [
        ("Features (feat)", "feat"),
        ("Bug Fixes (fix)", "fix"),
        ("Performance (perf)", "perf"),
        ("Breaking Change (!)", "breaking"),
        ("Documentation (docs)", "docs"),
        ("Refactoring (refactor)", "refactor"),
        ("Maintenance (chore)", "chore"),
        ("Security (security)", "security"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="reclassify-dialog"):
            yield Label("Select Target Section / Type:")
            options = [Option(label, id=val) for label, val in self.TYPES]
            yield OptionList(*options, id="type-options")
            yield Label("[dim]Enter to select, Esc to cancel[/dim]")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option_id)

    def key_escape(self) -> None:
        self.dismiss(None)
