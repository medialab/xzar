from typing import Annotated, IO

from ..argparse import TypicalTypedArgs, Arg, ImplicitInputArg
from ..transformers_models import SentenceTransformersLang


class EmbedArgs(TypicalTypedArgs):
    column: Annotated[
        str,
        Arg(
            help="column of CSV file containing text from which to create embeddings",
            positional=True,
        ),
    ]
    input: Annotated[IO[str], ImplicitInputArg()]
    lang: Annotated[
        SentenceTransformersLang,
        Arg(
            "-l",
            default="en",
            help="lang for the sentence-transformers model to use.",
        ),
    ]
    npy: Annotated[bool, Arg(help="npy")]


def embed(args: EmbedArgs):
    print(args)
    return
