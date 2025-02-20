from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from spacy.language import Language

SpacyModelSize = Literal["sm", "md", "lg", "trf"]
SpacyLang = Literal[
    "de",
    "en",
    "fr",
]

MODEL_TYPE_PER_LANG: dict[SpacyLang, str] = {
    "de": "news",
    "en": "web",
    "fr": "news",
}
MODEL_TRF_DEP_LANG = {"de", "fr"}


def get_spacy_model_handle(lang: SpacyLang, size: SpacyModelSize) -> str:
    model_type = MODEL_TYPE_PER_LANG[lang]
    model_core = "dep" if size == "trf" and lang in MODEL_TRF_DEP_LANG else "core"

    return f"{lang}_{model_core}_{model_type}_{size}"


SPICY_PIPELINE_COMPONENTS = [
    "tagger",
    "parser",
    "entity_linker",
    "entity_ruler",
    "textcat",
    "textcat_multilabel",
    "lemmatizer",
    "trainable_lemmatizer",
    "ner",
    "morphologizer",
    "attribute_ruler",
    "senter",
    "sentencizer",
    "tok2vec",
    "transformer",
]


def get_spacy_exclude(include: list[str]) -> list[str]:
    return [c for c in SPICY_PIPELINE_COMPONENTS if c not in include]


def acquire_model(
    lang: SpacyLang, size: SpacyModelSize, include: list[str]
) -> "Language":
    import sys
    import spacy
    from contextlib import redirect_stdout

    spacy_model_handle = get_spacy_model_handle(lang, size)
    spacy_exclude = get_spacy_exclude(include)

    try:
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)
    except OSError:
        with redirect_stdout(sys.stderr):
            spacy.cli.download(spacy_model_handle, False, False, "--quiet")  # type: ignore
        nlp = spacy.load(spacy_model_handle, exclude=spacy_exclude)

    return nlp
