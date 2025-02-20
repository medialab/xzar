import types
from typing import (
    cast,
    Iterable,
    Type,
    Callable,
    TypeVar,
    Literal,
    IO,
    Annotated,
    get_type_hints,
    get_args,
    get_origin,
)

import sys
import argparse
from rich_argparse import RichHelpFormatter
from dataclasses import dataclass


def snake_case_to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


def get_arg_type_hints(args: Type) -> dict[str, tuple["Arg", Type]]:
    hints = get_type_hints(args, include_extras=True)
    mapped_hints = {}

    for name, arg_type in hints.items():
        if (
            not hasattr(arg_type, "__metadata__")
            or len(arg_type.__metadata__) != 1
            or not isinstance(arg_type.__metadata__[0], Arg)
        ):
            raise TypeError("cli args should be correctly annotated with an Arg!")

        arg = cast(Arg, arg_type.__metadata__[0])
        origin = arg_type.__origin__

        mapped_hints[name] = (arg, origin)

    return mapped_hints


def get_optional_type(t):
    if get_origin(t) is not types.UnionType:
        return

    args = get_args(t)

    if len(args) == 2 and get_origin(args[0]) is None:
        return args[0]

    return


class Arg:
    short_flag: str | None = None
    help: str | None = None
    default: str | None = None
    nargs: str | None = None
    positional: bool = False

    def __init__(
        self,
        short_flag: str | None = None,
        help: str | None = None,
        default: str | None = None,
        nargs: str | None = None,
        positional: bool = False,
    ):
        self.short_flag = short_flag
        self.help = help
        self.default = default
        self.nargs = nargs
        self.positional = positional


class ImplicitInputArg(Arg):
    def __init__(self):
        self.nargs = "?"
        self.default = "-"
        self.help = "path to CSV file input. Will default to stdin if not given."
        self.positional = True

    def bind(self, value) -> IO[str]:
        if value == "-":
            return sys.stdin

        return open(value, "r")


class ImplicitOutputArg(Arg):
    def __init__(self):
        self.short_flag = "-o"
        self.help = 'write output to path instead of priting to stdout. Passing "-" as a path will also be understood as a shorthand for stdout.'
        self.default = "-"

    def bind(self, value) -> IO[str]:
        if value == "-":
            return sys.stdout

        return open(value, "w")


T = TypeVar("T")


@dataclass
class SubCommand[T]:
    name: str
    args: Type
    fn: Callable[[T], None]
    help: str | None = None
    description: str | None = None


def create_parser(
    prog: str, subcommands: Iterable[SubCommand]
) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog, formatter_class=RichHelpFormatter)
    subparsers = parser.add_subparsers(title="subcommands")

    for subcommand in subcommands:
        subparser = subparsers.add_parser(
            subcommand.name,
            help=subcommand.help,
            description=subcommand.description,
            formatter_class=RichHelpFormatter,
        )

        for name, (arg, origin) in get_arg_type_hints(subcommand.args).items():
            flags = []
            subparser_kwargs = {}

            if arg.short_flag is not None:
                flags.append(arg.short_flag)

            flags.append(
                ("--" if not arg.positional else "") + snake_case_to_kebab_case(name)
            )

            if get_origin(origin) is Literal:
                subparser_kwargs["choices"] = get_args(origin)

            if arg.help is not None:
                subparser_kwargs["help"] = arg.help.rstrip(".") + "."
                if arg.default is not None and not isinstance(
                    arg, (ImplicitOutputArg, ImplicitInputArg)
                ):
                    subparser_kwargs["help"] += " Defaults to {!r}.".format(arg.default)

            if origin is int or get_optional_type(origin) is int:
                subparser_kwargs["type"] = int

            elif origin is float or get_optional_type(origin) is float:
                subparser_kwargs["type"] = float

            if origin is bool:
                subparser_kwargs["action"] = "store_true"
            else:
                subparser_kwargs["default"] = arg.default
                subparser_kwargs["nargs"] = arg.nargs

            subparser.add_argument(*flags, **subparser_kwargs)
            subparser.set_defaults(__fn=subcommand.fn, __args=subcommand.args)

    return parser


class TypedArgs:
    def __repr__(self) -> str:
        return "{}({})".format(
            self.__class__.__name__,
            ", ".join(
                "{}={!r}".format(name, value) for name, value in vars(self).items()
            ),
        )


class TypicalTypedArgs(TypedArgs):
    total: Annotated[
        int | None,
        Arg(
            help="total number of items to process. Might be necessary when you want to display a finite progress indicator for large files given as input to the command."
        ),
    ]
    output: Annotated[IO[str], ImplicitOutputArg()]


def bind_namespace_to_args(namespace: argparse.Namespace, args_class: Type[T]) -> T:
    args = args_class()
    hints = get_arg_type_hints(args_class)

    for name, value in vars(namespace).items():
        if name.startswith("__"):
            continue

        hint, _ = hints[name]

        if hasattr(hint, "bind"):
            value = hint.bind(value)  # type: ignore

        # TODO: we could validate type here to avoid shenanigans
        setattr(args, name, value)

    return args


# Tests
if __name__ == "__main__":
    Lang = Literal["fr", "en"]

    class NerArgs(TypicalTypedArgs):
        lang: Annotated[Lang, Arg("-l", help="lang for the model.", default="en")]

    def ner(args: NerArgs):
        print("NER!")
        print(args)

    class TokenizeArgs(TypicalTypedArgs):
        model_size: Annotated[str, Arg("-M", help="size for the Spacy model")]

    def tokenize(args: TokenizeArgs):
        print("TOKENIZE")
        print(args)

    commands = [
        SubCommand(
            "ner",
            NerArgs,
            ner,
            help="Named entity recognition",
            description="Perform named entity recognition using spacy.",
        ),
        SubCommand(
            "tokenize",
            TokenizeArgs,
            tokenize,
            help="Tokenization",
            description="Tokenize with Spacy",
        ),
    ]

    parser = create_parser("xzar", commands)
    args = parser.parse_args()

    if not hasattr(args, "__args"):
        parser.print_help()
    else:
        bound_args = bind_namespace_to_args(args, args.__args)
        args.__fn(bound_args)
