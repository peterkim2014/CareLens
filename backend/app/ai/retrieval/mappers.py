from app.ai.retrieval.schemas import EvidenceDocument
from app.db.models import EvidenceDocumentModel


def map_evidence_document(
    model: EvidenceDocumentModel,
) -> EvidenceDocument:
    metadata: dict[str, str] = {}

    if model.source_url is not None:
        metadata["source_url"] = model.source_url

    if model.publication_date is not None:
        metadata["publication_date"] = model.publication_date.isoformat()

    if model.specialty is not None:
        metadata["specialty"] = model.specialty

    if model.keywords:
        metadata["keywords"] = ",".join(model.keywords)

    return EvidenceDocument(
        document_id=model.external_id,
        title=model.title,
        content=model.content,
        source=model.source_name,
        source_type="reviewed_evidence",
        metadata=metadata,
    )
