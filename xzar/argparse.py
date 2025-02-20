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
    Any,
    get_type_hints,
    get_args,
    get_origin,
)

import sys
import argparse
from rich_argparse import RichHelpFormatter
from dataclasses import dataclass
from casanova import RowCountResumer

from .exceptions import ResolvingError
from .utils import acquire_cross_platform_stdout

# Typed argparse workflow:
#   1. we create an argument parser from a series of subcommands
#      that contains typed annotated arguments.
#   2. we parse the command line arguments with it.
#   3. we instantiate and "bind" the typed arguments class.
#   4. we "resolve" the typed arguments. At that point we have
#      access to all the bound arguments and we can validate
#      them dependently and wrangle them if needed.


RichHelpFormatter.highlights = [
    r"(?P<args>-[a-zA-Z])[\s/.]",  # -f flags
    r"(?P<args>--[a-z]+(-[a-z]+)*)[\s/.]",  # --flag flags
    r'(?P<metavar>"[^"]+")',  # double-quote literals
    r"(?P<metavar>`[^`]+`)",  # backtick literals
    r"(?P<args>https?://\S+)",  # urls
]


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


ArgparseDefaultValue = str | int | float


class Arg:
    short_flag: str | None = None
    help: str | None = None
    default: ArgparseDefaultValue | None = None
    nargs: str | None = None
    positional: bool = False
    validate: Callable[[Any], None] | None = None

    def __init__(
        self,
        short_flag: str | None = None,
        help: str | None = None,
        default: ArgparseDefaultValue | None = None,
        nargs: str | None = None,
        positional: bool = False,
        validate: Callable[[Any], None] | None = None,
    ):
        self.short_flag = short_flag
        self.help = help
        self.default = default
        self.nargs = nargs
        self.positional = positional
        self.validate = validate


class ImplicitInputArg(Arg):
    def __init__(self):
        self.nargs = "?"
        self.default = "-"
        self.help = "path to CSV file input. Will default to stdin if not given."
        self.positional = True


class ImplicitOutputArg(Arg):
    def __init__(self):
        self.short_flag = "-o"
        self.help = 'writoutput_pathe output to path instead of priting to stdout. Passing "-" as a path will also be understood as a shorthand for stdout.'
        self.default = "-"


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
                    subparser_kwargs["help"] += ' Defaults to "{}".'.format(arg.default)

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

    def internal_resolve(self):
        raise NotImplementedError

    def resolve(self):
        raise NotImplementedError


class TypicalTypedArgs(TypedArgs):
    total: Annotated[
        int | None,
        Arg(
            help="total number of items to process. Might be necessary when you want to display a finite progress indicator for large files given as input to the command."
        ),
    ]
    output: Annotated[IO[str], ImplicitOutputArg()]

    def internal_resolve(self):
        try:
            input_path = cast(str, getattr(self, "input"))
        except AttributeError:
            raise TypeError(
                'could not find "input" attribute. Did you forget to add it?'
            )

        output_path = cast(str, getattr(self, "output"))

        resuming_io = None

        if hasattr(self, "resume") and getattr(self, "resume"):
            if output_path == "-":
                raise ResolvingError(
                    "cannot use --resume without knowing the output path through -o/--output!"
                )

            resuming_io = RowCountResumer(output_path)

        if input_path == "-":
            input_io = sys.stdin
        else:
            input_io = open(input_path, "r", encoding="utf-8")

        if output_path == "-":
            output_io = acquire_cross_platform_stdout()
        elif resuming_io is not None:
            output_io = resuming_io
        else:
            output_io = open(output_path, "w", encoding="utf-8", newline="")

        setattr(self, "input", input_io)
        setattr(self, "output", output_io)


def bind_namespace_to_args(namespace: argparse.Namespace, args_class: Type[T]) -> T:
    args = args_class()
    hints = get_arg_type_hints(args_class)

    for name, value in vars(namespace).items():
        if name.startswith("__"):
            continue

        hint, _ = hints[name]

        if hasattr(hint, "bind"):
            value = hint.bind(value)  # type: ignore

        if hint.validate is not None:
            hint.validate(value)

        # TODO: we could validate type here to avoid shenanigans
        setattr(args, name, value)

    return args


def resolve(args: TypedArgs):
    try:
        args.internal_resolve()
    except NotImplementedError:
        pass

    try:
        args.resolve()
    except NotImplementedError:
        pass


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
