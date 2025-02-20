from typing import Annotated, IO

import sys
from contextlib import redirect_stdout

import casanova
from casanova.headers import Selection, SingleColumn

from ..argparse import TypicalTypedArgs, Arg, ImplicitInputArg
from ..exceptions import ArgumentValidationError
from ..loading_bar import LoadingBar
from ..spacy_models import (
    SpacyLang,
    SpacyModelSize,
    get_spacy_model_handle,
    get_spacy_exclude,
)


def validate_processes(p: int):
    if p is not None and p < -1 or p == 0:
        raise ArgumentValidationError("-p/--processes should be positive or -1!")


class NerArgs(TypicalTypedArgs):
    column: Annotated[
        str,
        Arg(
            help="column of CSV file containing text from which to extract entities",
            positional=True,
        ),
    ]
    input: Annotated[IO[str], ImplicitInputArg()]
    lang: Annotated[
        SpacyLang,
        Arg(
            "-l",
            default="en",
            help="lang for the spacy model to use.",
        ),
    ]
    model_size: Annotated[
        SpacyModelSize,
        Arg("-M", default="sm", help="size of Spacy model to use."),
    ]
    processes: Annotated[
        int,
        Arg(
            "-p",
            help="number of processes to use. Set to -1 to select a number of processes based on the currently available CPUs.",
            default="1",
            validate=validate_processes,
        ),
    ]
    batch_size: Annotated[
        int | None, Arg("-B", help="number of documents to process at once.")
    ]


def ner(args: NerArgs):
    import spacy

    spacy_model_handle = get_spacy_model_handle(args.lang, args.model_size)
    spacy_exclude = get_spacy_exclude(["ner"])

    try:
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)
    except OSError:
        with redirect_stdout(sys.stderr):
            spacy.cli.download(spacy_model_handle, False, False, "--quiet")  # type: ignore
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)

    selection = Selection(inverted=True)
    selection.add(SingleColumn(args.column))

    enricher = casanova.enricher(
        args.input, args.output, add=["entity", "entity_type"], select=selection
    )

    def tuples():
        for row, text in enricher.cells(args.column, with_rows=True):
            yield text, row

    with LoadingBar.from_reader(
        enricher, "Extracting", total=args.total
    ) as loading_bar:
        for doc, row in nlp.pipe(
            tuples(),
            as_tuples=True,
            n_process=args.processes,
            batch_size=args.batch_size,
        ):
            for entity in doc.ents:
                enricher.writerow(row, [entity.text, entity.label_])

            loading_bar.advance()
