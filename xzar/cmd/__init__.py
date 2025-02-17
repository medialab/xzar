from ..argparse import SubCommand

from .ner import NerArgs, ner
from .tokenize import TokenizeArgs, tokenize

SUBCOMMANDS = [
    SubCommand("ner", args=NerArgs, fn=ner),
    SubCommand("tokenize", args=TokenizeArgs, fn=tokenize),
]

__all__ = ["SUBCOMMANDS"]
