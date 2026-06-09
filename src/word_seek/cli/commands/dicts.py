from curtsies.formatstring import fmtstr

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
