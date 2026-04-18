from fastapi import APIRouter, Depends

from app.db.models import User
from app.deps import get_current_user
from app.schemas.api import EducationRequest, EducationResponse, SourceChunk
from app.services.rag import run_rag

router = APIRouter(prefix="/education", tags=["education"])


@router.post("/ask", response_model=EducationResponse)
def ask(body: EducationRequest, current: User = Depends(get_current_user)):
    answer, chunks, low = run_rag(body.question.strip())
    sources = [
        SourceChunk(
            content_preview=c["content_preview"],
            score=c["score"],
            metadata=c["metadata"],
            file_name=c.get("file_name", ""),
            page=int(c.get("page", 1)),
            highlight=c.get("highlight", ""),
        )
        for c in chunks
    ]
    return EducationResponse(answer=answer, sources=sources, low_confidence=low)
