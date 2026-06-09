import sys

ESCAPED_ENDLINE = "\\\n"

sys.stdout.writelines(
    line.removesuffix(ESCAPED_ENDLINE) for line in sys.stdin.readlines()
)
