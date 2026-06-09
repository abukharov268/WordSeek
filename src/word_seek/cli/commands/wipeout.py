from rich.prompt import Confirm

from ...db.scaffold import wipeout


async def wipeout_db() -> None:
    if Confirm.ask("Are you sure you want to DELETE database?"):
        await wipeout()
