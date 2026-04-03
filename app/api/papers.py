from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.paper import Paper
from app.schemas.paper import PaperOut

router = APIRouter(prefix="/papers", tags=["papers"])


@router.get("", response_model=list[PaperOut])
async def list_papers(
    query: str = Query("", description="Search by title"),
    year: int | None = Query(None),
    venue: str | None = Query(None),
    sort_by: str = Query("citation_count", enum=["citation_count", "year", "title"]),
    order: str = Query("desc", enum=["asc", "desc"]),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Paper)

    if query:
        stmt = stmt.where(Paper.title.ilike(f"%{query}%"))
    if year:
        stmt = stmt.where(Paper.year == year)
    if venue:
        stmt = stmt.where(Paper.venue.ilike(f"%{venue}%"))

    sort_col = getattr(Paper, sort_by, Paper.citation_count)
    stmt = stmt.order_by(sort_col.desc() if order == "desc" else sort_col.asc())
    stmt = stmt.offset(offset).limit(limit)

    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/top-cited", response_model=list[PaperOut])
async def top_cited_papers(
    limit: int = Query(20, le=100),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Paper).order_by(Paper.citation_count.desc()).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
