from ..utils import xzar


class TestNerCommand:
    def test_basics(self):
        assert xzar(["ner", "text"], [["text"], ["Barack Obama went to Austria."]]) == [
            ["entity", "entity_type"],
            ["Barack Obama", "PERSON"],
            ["Austria", "GPE"],
        ]
