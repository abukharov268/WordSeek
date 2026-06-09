from sqlalchemy.sql import ColumnExpressionArgument
from sqlalchemy.sql.expression import func
from sqlalchemy.sql.functions import Function


def instr(
    target_string: str | ColumnExpressionArgument, term: str | ColumnExpressionArgument
) -> Function:
    return func.instr(target_string, term)
