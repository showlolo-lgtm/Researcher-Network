from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.institution import Institution
from app.models.researcher import Researcher
from app.schemas.researcher import ResearcherOut

router = APIRouter(prefix="/researchers", tags=["researchers"])


@router.get("", response_model=list[ResearcherOut])
async def list_researchers(
    query: str = Query("", description="Search by name"),
    institution_id: int | None = Query(None),
    research_area: str | None = Query(None),
    min_h_index: int | None = Query(None),
    sort_by: str = Query("h_index", enum=["h_index", "citation_count", "paper_count", "name"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Researcher).options(joinedload(Researcher.affiliation))

    if query:
        stmt = stmt.where(Researcher.name.ilike(f"%{query}%"))
    if institution_id:
        stmt = stmt.where(Researcher.affiliation_id == institution_id)
    if research_area:
        # JSON array contains check for SQLite
        stmt = stmt.where(Researcher.research_areas.contains(research_area))
    if min_h_index:
        stmt = stmt.where(Researcher.h_index >= min_h_index)

    sort_col = getattr(Researcher, sort_by, Researcher.h_index)
    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    researchers = result.unique().scalars().all()

    return [
        ResearcherOut(
            id=r.id,
            name=r.name,
            name_zh=r.name_zh,
            semantic_scholar_id=r.semantic_scholar_id,
            affiliation_id=r.affiliation_id,
            affiliation_name=r.affiliation.name if r.affiliation else None,
            h_index=r.h_index,
            citation_count=r.citation_count,
            paper_count=r.paper_count,
            research_areas=r.research_areas or [],
            homepage_url=r.homepage_url,
            last_updated_at=r.last_updated_at,
        )
        for r in researchers
    ]


@router.get("/{researcher_id}", response_model=ResearcherOut)
async def get_researcher(researcher_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(Researcher).options(joinedload(Researcher.affiliation)).where(
        Researcher.id == researcher_id
    )
    result = await db.execute(stmt)
    r = result.unique().scalar_one()
    return ResearcherOut(
        id=r.id,
        name=r.name,
        name_zh=r.name_zh,
        semantic_scholar_id=r.semantic_scholar_id,
        affiliation_id=r.affiliation_id,
        affiliation_name=r.affiliation.name if r.affiliation else None,
        h_index=r.h_index,
        citation_count=r.citation_count,
        paper_count=r.paper_count,
        research_areas=r.research_areas or [],
        homepage_url=r.homepage_url,
        last_updated_at=r.last_updated_at,
    )


@router.get("/stats/summary")
async def researcher_stats(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.count(Researcher.id),
            func.avg(Researcher.h_index),
            func.max(Researcher.h_index),
            func.sum(Researcher.citation_count),
        )
    )
    row = result.one()
    return {
        "total_researchers": row[0],
        "avg_h_index": round(row[1], 1) if row[1] else 0,
        "max_h_index": row[2] or 0,
        "total_citations": row[3] or 0,
    }
