from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.schemas.institution import InstitutionOut

router = APIRouter(prefix="/institutions", tags=["institutions"])


@router.get("", response_model=list[InstitutionOut])
async def list_institutions(
    type: str | None = Query(None, enum=["university", "research_institute", "company"]),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Institution)
    if type:
        stmt = stmt.where(Institution.type == type)
    stmt = stmt.order_by(Institution.name)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{institution_id}/researchers")
async def institution_researchers(
    institution_id: int, db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Researcher)
        .where(Researcher.affiliation_id == institution_id)
        .order_by(Researcher.h_index.desc())
    )
    result = await db.execute(stmt)
    researchers = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "h_index": r.h_index,
            "citation_count": r.citation_count,
            "research_areas": r.research_areas or [],
        }
        for r in researchers
    ]


@router.get("/stats/distribution")
async def institution_distribution(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Institution.name, Institution.type, func.count(Researcher.id))
        .join(Researcher, Researcher.affiliation_id == Institution.id, isouter=True)
        .group_by(Institution.id)
        .order_by(func.count(Researcher.id).desc())
    )
    result = await db.execute(stmt)
    return [
        {"name": row[0], "type": row[1], "researcher_count": row[2]}
        for row in result.all()
    ]
