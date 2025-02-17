from typing import Annotated, IO

from ..argparse import TypicalTypedArgs, Arg, ImplicitInputArg
from ..spacy_models import SpacyLang


class TokenizeArgs(TypicalTypedArgs):
    lang: Annotated[SpacyLang, Arg("-l", default="en")]
    input: Annotated[IO[str], ImplicitInputArg()]


def tokenize(args: TokenizeArgs):
    print(args)
    return
