import os
import csv
import sys
import ctypes
from functools import wraps

import casanova
from rich_argparse import RichHelpFormatter
from typed_argparse import Parser, SubParserGroup

from .cmd import SUBPARSERS


def global_setup() -> None:
    csv.field_size_limit(int(ctypes.c_ulong(-1).value // 2))

    # Casanova global defaults
    casanova.set_defaults(
        strip_null_bytes_on_read=True,
        strip_null_bytes_on_write=True,
    )


def redirect_to_devnull():
    # Taken from: https://docs.python.org/3/library/signal.html
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, sys.stdout.fileno())


def with_cli_exceptions(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            fn(*args, **kwargs)

        except KeyboardInterrupt:
            redirect_to_devnull()
            sys.exit(1)

        except BrokenPipeError:
            redirect_to_devnull()
            sys.exit(1)

        except Exception:
            raise

    return wrapper


@with_cli_exceptions
def main() -> None:
    global_setup()

    # Dirty monkey patching
    from argparse import _SubParsersAction

    old_add_parser = _SubParsersAction.add_parser

    def new_add_parser(self, *args, **kwargs):
        kwargs["formatter_class"] = RichHelpFormatter
        return old_add_parser(self, *args, **kwargs)

    _SubParsersAction.add_parser = new_add_parser

    parser = Parser(
        SubParserGroup(*[subparser for subparser, _ in SUBPARSERS.values()]),
        prog="xzar",
        formatter_class=RichHelpFormatter,
    )

    parser.bind(*[fn for _, fn in SUBPARSERS.values()]).run()


if __name__ == "__main__":
    main()
