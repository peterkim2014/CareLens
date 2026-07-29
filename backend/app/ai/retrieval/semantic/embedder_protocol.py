from typing import Protocol


class Embedder(Protocol):
    @property
    def model_name(self) -> str:
        """Return the identifier of the embedding model."""
        ...

    def embed(
        self,
        text: str,
    ) -> list[float]:
        """Create an embedding for one text value."""
        ...

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        """Create embeddings for multiple text values."""
        ...
