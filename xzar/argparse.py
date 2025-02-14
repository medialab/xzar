from typing import (
    cast,
    Iterable,
    Type,
    Callable,
    TypeVar,
    Literal,
    get_type_hints,
    get_args,
    get_origin,
)

import argparse
from rich_argparse import RichHelpFormatter
from dataclasses import dataclass


def snake_case_to_kebab_case(string: str) -> str:
    return string.replace("_", "-")


class Arg:
    short_flag: str | None
    help: str | None
    default: str | None

    def __init__(
        self,
        short_flag: str | None = None,
        help: str | None = None,
        default: str | None = None,
    ):
        self.short_flag = short_flag
        self.help = help
        self.default = default


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

        hints = get_type_hints(subcommand.args, include_extras=True)

        for name, arg_type in hints.items():
            if (
                not hasattr(arg_type, "__metadata__")
                or len(arg_type.__metadata__) != 1
                or not isinstance(arg_type.__metadata__[0], Arg)
            ):
                raise TypeError("cli arg should be correctly annotated with an Arg!")

            flags = []
            arg = cast(Arg, arg_type.__metadata__[0])

            if arg.short_flag is not None:
                flags.append(arg.short_flag)

            flags.append("--" + snake_case_to_kebab_case(name))

            choices = None

            if get_origin(arg_type.__origin__) is Literal:
                choices = get_args(arg_type.__origin__)

            subparser.add_argument(
                *flags, help=arg.help, choices=choices, default=arg.default
            )
            subparser.set_defaults(__fn=subcommand.fn, __args=subcommand.args)

    return parser


def bind_namespace_to_args(namespace: argparse.Namespace, args_class: Type[T]) -> T:
    args = args_class()

    return args


# Tests
if __name__ == "__main__":
    from typing import Annotated

    Lang = Literal["fr", "en"]

    class NerArgs:
        lang: Annotated[Lang, Arg("-l", help="lang for the model", default="en")]

    def ner(args: NerArgs):
        pass

    class TokenizeArgs:
        model_size: Annotated[str, Arg("-M", help="size for the Spacy model")]

    def tokenize(args: TokenizeArgs):
        pass

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
    args = bind_namespace_to_args(args, args.__args)

    # todo: bind, and stringify
    print(args)
