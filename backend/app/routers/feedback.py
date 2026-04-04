from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import FeedbackEntry, User
from app.db.session import get_db
from app.deps import get_current_user
from app.schemas.api import FeedbackCreate, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    body: FeedbackCreate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    row = FeedbackEntry(
        user_id=current.id,
        message_id=body.message_id,
        rating=body.rating,
        comment=body.comment,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return FeedbackResponse(id=row.id)
