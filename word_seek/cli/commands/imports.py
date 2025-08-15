from pathlib import Path

from rich import markup
from rich.progress import Progress

from ...db.config import ensure_db
from ...importer import ImportProgress, ProgressCategory, bulk_import


async def import_dir(directory: Path) -> None:
    await ensure_db()
    with Progress() as progress:
        task = progress.add_task("Importing...", total=100)
        async for step in bulk_import(directory):
            progress.update(
                task,
                total=step.total,
                completed=step.num,
                description=f"Importing... | {step.name}",
            )
            print_msg(progress, step)

        progress.update(task, total=100, completed=100, description="Importing...")


def print_msg(progress: Progress, step: ImportProgress) -> None:
    match step.category:
        case ProgressCategory.WARN:
            style = "yellow"
        case ProgressCategory.ERROR:
            style = "red"
        case ProgressCategory.SKIP:
            style = "bright_black"
        case _:
            return
    progress.console.print(markup.escape(f"{step.msg} | {step.name}"), style=style)
