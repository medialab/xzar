from typing import Literal

SentenceTransformersLang = Literal[
    "de",
    "en",
    "fr",
]

MODEL_TYPE_PER_LANG: dict[SentenceTransformersLang, str] = {
    "de": "paraphrase-multilingual-MiniLM-L12-v2",
    "fr": "Lajavaness/sentence-flaubert-base",
    "en": "all-MiniLM-L6-v2",
}
