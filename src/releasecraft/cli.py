import typer

app = typer.Typer(
    name="releasecraft",
    help="Semantic Git release manager and changelog engine with interactive TUI",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Show ReleaseCraft version."""
    import releasecraft

    typer.echo(f"releasecraft v{releasecraft.__version__}")


if __name__ == "__main__":
    app()
