import hashlib

from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.schemas import (
    EvidenceDocument,
)
from app.ai.retrieval.semantic.embedder_protocol import (
    Embedder,
)
from app.ai.retrieval.semantic.repository_protocol import (
    VectorRepository,
)
from app.ai.retrieval.semantic.schemas import (
    EmbeddingRecord,
    SemanticIndexingResult,
)


class SemanticIndexingService:
    def __init__(
        self,
        evidence_repository: EvidenceRepository,
        embedder: Embedder,
        vector_repository: VectorRepository,
        *,
        batch_size: int = 100,
    ) -> None:
        if batch_size < 1:
            raise ValueError(
                "batch_size must be at least 1.",
            )

        self._evidence_repository = evidence_repository
        self._embedder = embedder
        self._vector_repository = vector_repository
        self._batch_size = batch_size

    def rebuild_index(
        self,
    ) -> SemanticIndexingResult:
        documents = self._evidence_repository.list_documents()

        current_document_ids = {document.document_id for document in documents}

        stored_document_ids = self._vector_repository.list_document_ids()

        stale_document_ids = stored_document_ids - current_document_ids

        self._vector_repository.delete_many(
            stale_document_ids,
        )

        documents_to_index: list[
            tuple[
                EvidenceDocument,
                str,
                str,
            ]
        ] = []

        skipped_documents = 0

        for document in documents:
            embedding_text = _build_embedding_text(
                document,
            )

            if not embedding_text.strip():
                skipped_documents += 1
                continue

            content_hash = _create_content_hash(
                embedding_text,
            )

            if self._vector_repository.contains_current_embedding(
                document.document_id,
                embedding_model=self._embedder.model_name,
                content_hash=content_hash,
            ):
                skipped_documents += 1
                continue

            documents_to_index.append(
                (
                    document,
                    embedding_text,
                    content_hash,
                )
            )

        records: list[EmbeddingRecord] = []

        for batch_start in range(
            0,
            len(documents_to_index),
            self._batch_size,
        ):
            batch = documents_to_index[batch_start : batch_start + self._batch_size]

            texts = [
                embedding_text
                for (
                    _,
                    embedding_text,
                    _,
                ) in batch
            ]

            embeddings = self._embedder.embed_many(
                texts,
            )

            if len(embeddings) != len(batch):
                raise RuntimeError(
                    "Embedder returned an unexpected number of embeddings.",
                )

            for (
                document,
                _,
                content_hash,
            ), embedding in zip(
                batch,
                embeddings,
                strict=True,
            ):
                if not embedding:
                    skipped_documents += 1
                    continue

                records.append(
                    EmbeddingRecord(
                        document_id=document.document_id,
                        embedding=embedding,
                        embedding_model=(self._embedder.model_name),
                        content_hash=content_hash,
                    )
                )

        self._vector_repository.upsert_many(
            records,
        )

        return SemanticIndexingResult(
            total_documents=len(documents),
            indexed_documents=len(records),
            skipped_documents=skipped_documents,
        )

    def index_document(
        self,
        document: EvidenceDocument,
    ) -> bool:
        embedding_text = _build_embedding_text(
            document,
        )

        if not embedding_text.strip():
            return False

        embedding = self._embedder.embed(
            embedding_text,
        )

        if not embedding:
            return False

        self._vector_repository.upsert(
            EmbeddingRecord(
                document_id=document.document_id,
                embedding=embedding,
                embedding_model=self._embedder.model_name,
                content_hash=_create_content_hash(
                    embedding_text,
                ),
            )
        )

        return True

    def remove_document(
        self,
        document_id: str,
    ) -> bool:
        return self._vector_repository.delete(
            document_id,
        )


def _create_content_hash(
    content: str,
) -> str:
    return hashlib.sha256(
        content.encode("utf-8"),
    ).hexdigest()


def _build_embedding_text(
    document: EvidenceDocument,
) -> str:
    keywords = document.metadata.get(
        "keywords",
        "",
    )
    specialty = document.metadata.get(
        "specialty",
        "",
    )

    return "\n".join(
        part
        for part in (
            document.title,
            str(keywords),
            str(specialty),
            document.content,
        )
        if part
    )
