from typing import Annotated, IO
import casanova
from ebbe import as_chunks

from ..argparse import TypicalTypedArgs, Arg, ImplicitInputArg
from ..loading_bar import LoadingBar


class EmbedArgs(TypicalTypedArgs):
    column: Annotated[
        str,
        Arg(
            help="column of CSV file containing text from which to create embeddings",
            positional=True,
        ),
    ]
    column_prefix: Annotated[
        str,
        Arg(
            help="prefix used to identify embedding columns in the resulting CSV file",
            default="dim_",
        ),
    ]
    input: Annotated[IO[str], ImplicitInputArg()]
    model: Annotated[
        str,
        Arg(
            "-m",
            help="sentence-transformers model name in the Hugging Face hub "
            "(https://huggingface.co/models?library=sentence-transformers) "
            "or path to a model on disc.",
            default="ibm-granite/granite-embedding-107m-multilingual",
        ),
    ]
    npy: Annotated[
        bool,
        Arg(help="output a .npy file instead of a CSV. If set, --output is required."),
    ]
    batch_size: Annotated[
        int,
        Arg("-B", help="number of documents to process at once.", default=128),
    ]
    resume: Annotated[
        bool,
        Arg(
            help="Whether to resume from an aborted collection. Need -o/--output to be set."
        ),
    ]


def embed(args: EmbedArgs):
    from sentence_transformers import SentenceTransformer

    transformer = SentenceTransformer(args.model)

    embedding_size = transformer.get_sentence_embedding_dimension()

    assert embedding_size is not None

    enricher = casanova.enricher(
        args.input,
        args.output,
        add=[args.column_prefix + str(i) for i in range(embedding_size)],
    )

    with LoadingBar.from_reader(enricher, "Embedding", args.total) as loading_bar:
        for chunk in as_chunks(
            args.batch_size, enricher.cells(args.column, with_rows=True)
        ):
            embeddings = transformer.encode(
                [c[1] for c in chunk], batch_size=args.batch_size
            )
            for row, embedding in zip(chunk, embeddings):
                enricher.writerow(row[0], embedding)
                loading_bar.advance()
