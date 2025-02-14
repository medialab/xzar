import sys
from contextlib import redirect_stdout

import casanova
from casanova.headers import Selection, SingleColumn
from typed_argparse import TypedArgs, arg

from ..spacy_models import (
    SpacyLang,
    SpacyModelSize,
    get_spacy_model_handle,
    get_spacy_exclude,
)


# TODO: either subclass TypedArgs to get optional positional and open files with __del__ or not
class NerArgs(TypedArgs):
    column: str = arg(positional=True)
    input: str = arg(positional=True)
    lang: SpacyLang = arg(
        "-l",
        default="en",
        help='lang for the spacy model to use. Will default to "en".',
    )
    model_size: SpacyModelSize = arg(
        "-M", default="sm", help='size of Spacy model to use. Will default to "sm".'
    )
    # output: str | None = arg("-o")


def ner(args: NerArgs):
    import spacy

    spacy_model_handle = get_spacy_model_handle(args.lang, args.model_size)
    spacy_exclude = get_spacy_exclude(["ner"])

    try:
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)
    except OSError:
        with redirect_stdout(sys.stderr):
            spacy.cli.download(spacy_model_handle)  # type: ignore
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)

    input_file = open(args.input, "r")
    selection = Selection(inverted=True)
    selection.add(SingleColumn(args.column))

    enricher = casanova.enricher(
        input_file, sys.stdout, add=["entity", "entity_type"], select=selection
    )

    def tuples():
        for row, text in enricher.cells(args.column, with_rows=True):
            yield text, row

    # TODO: flag for batch size, flag -p and -t
    for doc, row in nlp.pipe(tuples(), as_tuples=True, n_process=-1, batch_size=16):
        for entity in doc.ents:
            enricher.writerow(row, [entity.text, entity.label_])
