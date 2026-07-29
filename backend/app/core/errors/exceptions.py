from uuid import UUID

from app.ai.observability import PipelineAudit


class AnalysisPipelineError(Exception):
    def __init__(
        self,
        *,
        trace_id: UUID,
        failed_stage: str,
        audit: PipelineAudit,
        retryable: bool,
    ) -> None:
        super().__init__(f"Analysis pipeline failed at stage: {failed_stage}")

        self.trace_id = trace_id
        self.failed_stage = failed_stage
        self.audit = audit
        self.retryable = retryable
