from curtsies.formatstring import fmtstr
from rich.prompt import Confirm

from ...db import repo


async def list_dicts() -> None:
    dicts = await repo.list_dicts()
    if not dicts:
        print(fmtstr("No dictionaries", fg="yellow"))
    for dct in dicts:
        order = dct.sort_order if dct.sort_order is not None else "∞"

        line = fmtstr(f"{dct.id:8} ", bold=True)
        line += fmtstr(dct.title, dark=True)
        line += fmtstr(f" [sort order: {order}]", bold=True)
        print(line)


async def sort_dict(dict_id: int, sort_order: int) -> None:
    await repo.sort_dict(dict_id, sort_order)
    print("Dictionary's sorted")


async def delete_dict(dict_id: int) -> None:
    dictionary = await repo.get_dict(dict_id)
    if Confirm.ask(f"Are you sure you want to DELETE {dictionary.title} ({dictionary.id})?"):
        await repo.delete_dict(dict_id)
        print("Dictionary's deleted")


async def delete_all_dicts() -> None:
    if Confirm.ask("Are you sure you want to DELETE ALL dictionaries and articles?"):
        await repo.delete_all_dicts()
        print("Dictionaries are deleted")
