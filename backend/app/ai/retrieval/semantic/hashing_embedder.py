import hashlib
import math
import re

TOKEN_PATTERN = re.compile(
    r"[a-z0-9]+",
)


class HashingEmbedder:
    def __init__(
        self,
        dimensions: int = 128,
    ) -> None:
        if dimensions < 1:
            raise ValueError(
                "dimensions must be at least 1.",
            )

        self._dimensions = dimensions

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return "hashing"

    def embed(
        self,
        text: str,
    ) -> list[float]:
        tokens = TOKEN_PATTERN.findall(
            text.lower(),
        )

        if not tokens:
            return []

        embedding = [0.0 for _ in range(self._dimensions)]

        for token in tokens:
            digest = hashlib.sha256(
                token.encode("utf-8"),
            ).digest()

            index = (
                int.from_bytes(
                    digest[:8],
                    byteorder="big",
                )
                % self._dimensions
            )

            sign = 1.0 if digest[8] % 2 == 0 else -1.0

            embedding[index] += sign

        return _normalize_embedding(
            embedding,
        )

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        return [self.embed(text) for text in texts]


def _normalize_embedding(
    embedding: list[float],
) -> list[float]:
    magnitude = math.sqrt(sum(value * value for value in embedding))

    if magnitude == 0.0:
        return embedding

    return [value / magnitude for value in embedding]
