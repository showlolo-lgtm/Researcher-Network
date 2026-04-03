from collections import Counter

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.institution import Institution
from app.models.paper import Paper
from app.models.relationship import Relationship
from app.models.researcher import Researcher

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/rankings")
async def rankings(
    sort_by: str = Query("h_index", enum=["h_index", "citation_count", "paper_count"]),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    sort_col = getattr(Researcher, sort_by, Researcher.h_index)
    stmt = (
        select(
            Researcher.id,
            Researcher.name,
            Researcher.h_index,
            Researcher.citation_count,
            Researcher.paper_count,
            Institution.name.label("affiliation"),
        )
        .join(Institution, Researcher.affiliation_id == Institution.id, isouter=True)
        .order_by(sort_col.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [
        {
            "rank": i + 1,
            "id": row[0],
            "name": row[1],
            "h_index": row[2],
            "citation_count": row[3],
            "paper_count": row[4],
            "affiliation": row[5],
        }
        for i, row in enumerate(result.all())
    ]


@router.get("/research-areas")
async def research_area_distribution(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Researcher.research_areas))
    counter = Counter()
    for (areas,) in result.all():
        if areas:
            for area in areas:
                counter[area] += 1

    return [{"area": area, "count": count} for area, count in counter.most_common(30)]


@router.get("/top-papers")
async def top_papers(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Paper).order_by(Paper.citation_count.desc()).limit(limit)
    result = await db.execute(stmt)
    papers = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "year": p.year,
            "venue": p.venue,
            "citation_count": p.citation_count,
            "fields": p.fields_of_study or [],
        }
        for p in papers
    ]


@router.get("/papers-by-year")
async def papers_by_year(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Paper.year, func.count(Paper.id), func.sum(Paper.citation_count))
        .where(Paper.year.isnot(None))
        .group_by(Paper.year)
        .order_by(Paper.year)
    )
    result = await db.execute(stmt)
    return [
        {"year": row[0], "paper_count": row[1], "total_citations": row[2] or 0}
        for row in result.all()
    ]


@router.get("/collaboration-stats")
async def collaboration_stats(db: AsyncSession = Depends(get_db)):
    # Most connected researchers
    stmt = (
        select(
            Researcher.id,
            Researcher.name,
            func.count(Relationship.id).label("connections"),
        )
        .join(
            Relationship,
            (Relationship.researcher_a_id == Researcher.id)
            | (Relationship.researcher_b_id == Researcher.id),
        )
        .group_by(Researcher.id)
        .order_by(func.count(Relationship.id).desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    return [
        {"id": row[0], "name": row[1], "connections": row[2]}
        for row in result.all()
    ]
