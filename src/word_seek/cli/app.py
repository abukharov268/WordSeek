import asyncio
from pathlib import Path

import typer

from . import commands as cmd

history_app = typer.Typer()
dicts_app = typer.Typer()
app = typer.Typer()
app.add_typer(history_app, name="history")
app.add_typer(dicts_app, name="dicts")


@app.command()
def import_dir(directory: Path):
    asyncio.run(cmd.import_dir(directory))


@app.command()
def wipeout_db():
    asyncio.run(cmd.wipeout_db())


@app.callback(invoke_without_command=True)
def enter_search(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        asyncio.run(cmd.enter_search())


@history_app.callback(invoke_without_command=True)
def history(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        asyncio.run(cmd.browse_history())


@history_app.command()
def clear():
    asyncio.run(cmd.clear_history())


@history_app.command()
def flush():
    asyncio.run(cmd.flush_history())


@dicts_app.command()
def list():
    asyncio.run(cmd.list_dicts())


@dicts_app.command()
def sort(id: int, order: int):
    asyncio.run(cmd.sort_dict(id, order))
