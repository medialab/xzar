import os
import csv
import sys
import ctypes
from functools import wraps

import casanova

from .cmd import SUBCOMMANDS
from .argparse import create_parser, bind_namespace_to_args


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
    parser = create_parser("xzar", SUBCOMMANDS)
    args = parser.parse_args()

    if not hasattr(args, "__args"):
        parser.print_help()
    else:
        bound_args = bind_namespace_to_args(args, args.__args)
        args.__fn(bound_args)


if __name__ == "__main__":
    main()
