from ..argparse import SubCommand

from .ner import NerArgs, ner
from .tokenize import TokenizeArgs, tokenize
from .embed import EmbedArgs, embed

SUBCOMMANDS = [
    SubCommand("ner", args=NerArgs, fn=ner),
    SubCommand("tokenize", args=TokenizeArgs, fn=tokenize),
    SubCommand("embed", args=EmbedArgs, fn=embed),
]

__all__ = ["SUBCOMMANDS"]
