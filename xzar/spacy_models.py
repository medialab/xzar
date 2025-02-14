from typing import Literal

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
