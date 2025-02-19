from ..utils import xzar

DEFAULT_EMBEDDING_SIZE = 384


class TestEmbedCommand:
    def test_basics(self):
        expected_headers = ["text"]
        expected_headers.extend("dim_" + str(i) for i in range(DEFAULT_EMBEDDING_SIZE))
        headers, row = xzar(
            ["embed", "text"], [["text"], ["Barack Obama went to Austria."]]
        )
        assert headers == expected_headers
        assert len(row[1:]) == DEFAULT_EMBEDDING_SIZE
        float(row[1])
