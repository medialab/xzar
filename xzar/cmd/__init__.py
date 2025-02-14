from typed_argparse import SubParser

from .ner import NerArgs, ner
from .tokenize import TokenizeArgs, tokenize

COMMANDS = [
    ("ner", NerArgs, ner),
    ("tokenize", TokenizeArgs, tokenize),
]
SUBPARSERS = {name: (SubParser(name, args), fn) for name, args, fn in COMMANDS}

__all__ = ["SUBPARSERS"]
