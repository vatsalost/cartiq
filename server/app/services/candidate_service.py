"""Candidate service for retrieving evaluated products and offers."""

from typing import List
import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from server.app.core.errors import CartiAPIException, CartiErrorCode
from server.app.models.candidate import Candidate
from server.app.models.request import ShoppingRequest


class CandidateService:
    """Retrieves candidates and offers with ownership validation."""

    def __init__(self, db: Session):
        self.db = db

    def get_candidates_for_request(
        self, request_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Candidate]:
        """Fetch all candidates for a request, ensuring the user owns the request."""
        req = self.db.get(ShoppingRequest, request_id)
        if not req:
            raise CartiAPIException(
                code=CartiErrorCode.REQUEST_NOT_FOUND,
                message=f"Shopping request {request_id} not found.",
                status_code=404,
            )
        if req.user_id != user_id:
            raise CartiAPIException(
                code=CartiErrorCode.ACCESS_DENIED,
                message="You do not have permission to view candidates for this request.",
                status_code=403,
            )

        stmt = (
            select(Candidate)
            .where(Candidate.request_id == request_id)
            .options(selectinload(Candidate.offers))
            .order_by(Candidate.rank_score.desc().nullslast())
        )
        return list(self.db.scalars(stmt).all())
