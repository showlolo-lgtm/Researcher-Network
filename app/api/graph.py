from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import get_db
from app.models.institution import Institution
from app.models.relationship import Relationship
from app.models.researcher import Researcher
from app.schemas.graph import GraphData, GraphLink, GraphNode

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("", response_model=GraphData)
async def get_graph(
    institution_id: int | None = Query(None),
    research_area: str | None = Query(None),
    min_h_index: int | None = Query(None),
    max_tier: int = Query(3, description="Max relationship tier to include (1=closest)"),
    limit: int = Query(200, le=1000, description="Max number of researchers"),
    db: AsyncSession = Depends(get_db),
):
    # Build researcher query
    stmt = select(Researcher).options(joinedload(Researcher.affiliation))

    if institution_id:
        stmt = stmt.where(Researcher.affiliation_id == institution_id)
    if research_area:
        stmt = stmt.where(Researcher.research_areas.contains(research_area))
    if min_h_index:
        stmt = stmt.where(Researcher.h_index >= min_h_index)

    stmt = stmt.order_by(Researcher.h_index.desc()).limit(limit)
    result = await db.execute(stmt)
    researchers = result.unique().scalars().all()

    researcher_ids = {r.id for r in researchers}

    # Build nodes
    nodes = [
        GraphNode(
            id=r.id,
            name=r.name,
            affiliation=r.affiliation.name if r.affiliation else None,
            h_index=r.h_index,
            citation_count=r.citation_count,
            research_areas=r.research_areas or [],
            institution_type=r.affiliation.type.value if r.affiliation else None,
        )
        for r in researchers
    ]

    # Get relationships between these researchers
    if researcher_ids:
        rel_stmt = (
            select(Relationship)
            .where(
                Relationship.researcher_a_id.in_(researcher_ids),
                Relationship.researcher_b_id.in_(researcher_ids),
                Relationship.tier <= max_tier,
            )
            .order_by(Relationship.tier, Relationship.weight.desc())
        )
        rel_result = await db.execute(rel_stmt)
        relationships = rel_result.scalars().all()
    else:
        relationships = []

    links = [
        GraphLink(
            source=r.researcher_a_id,
            target=r.researcher_b_id,
            type=r.type.value,
            tier=r.tier,
            weight=r.weight,
        )
        for r in relationships
    ]

    return GraphData(nodes=nodes, links=links)


@router.get("/ego/{researcher_id}", response_model=GraphData)
async def get_ego_graph(
    researcher_id: int,
    max_tier: int = Query(2),
    db: AsyncSession = Depends(get_db),
):
    """Get the ego network centered on a specific researcher."""
    # Find all relationships for this researcher
    rel_stmt = select(Relationship).where(
        or_(
            Relationship.researcher_a_id == researcher_id,
            Relationship.researcher_b_id == researcher_id,
        ),
        Relationship.tier <= max_tier,
    )
    rel_result = await db.execute(rel_stmt)
    relationships = rel_result.scalars().all()

    # Collect all connected researcher IDs
    connected_ids = {researcher_id}
    for r in relationships:
        connected_ids.add(r.researcher_a_id)
        connected_ids.add(r.researcher_b_id)

    # Fetch all connected researchers
    res_stmt = (
        select(Researcher)
        .options(joinedload(Researcher.affiliation))
        .where(Researcher.id.in_(connected_ids))
    )
    res_result = await db.execute(res_stmt)
    researchers = res_result.unique().scalars().all()

    nodes = [
        GraphNode(
            id=r.id,
            name=r.name,
            affiliation=r.affiliation.name if r.affiliation else None,
            h_index=r.h_index,
            citation_count=r.citation_count,
            research_areas=r.research_areas or [],
            institution_type=r.affiliation.type.value if r.affiliation else None,
        )
        for r in researchers
    ]

    links = [
        GraphLink(
            source=r.researcher_a_id,
            target=r.researcher_b_id,
            type=r.type.value,
            tier=r.tier,
            weight=r.weight,
        )
        for r in relationships
    ]

    return GraphData(nodes=nodes, links=links)
