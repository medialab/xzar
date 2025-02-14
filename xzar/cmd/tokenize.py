from typed_argparse import TypedArgs, arg


class TokenizeArgs(TypedArgs):
    lang: str = arg("-l", default="en")


def tokenize(args: TokenizeArgs):
    print(args)
