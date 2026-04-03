from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.relationship import Relationship
from app.schemas.relationship import RelationshipOut

router = APIRouter(prefix="/relationships", tags=["relationships"])


@router.get("", response_model=list[RelationshipOut])
async def list_relationships(
    researcher_id: int | None = Query(None, description="Filter by researcher"),
    type: str | None = Query(None),
    min_tier: int | None = Query(None),
    limit: int = Query(100, le=1000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Relationship)

    if researcher_id:
        stmt = stmt.where(
            or_(
                Relationship.researcher_a_id == researcher_id,
                Relationship.researcher_b_id == researcher_id,
            )
        )
    if type:
        stmt = stmt.where(Relationship.type == type)
    if min_tier:
        stmt = stmt.where(Relationship.tier <= min_tier)

    stmt = stmt.order_by(Relationship.tier, Relationship.weight.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
