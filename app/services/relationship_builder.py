import logging
from collections import defaultdict
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.paper import researcher_paper
from app.models.relationship import Relationship, RelationshipType
from app.models.researcher import Researcher

logger = logging.getLogger(__name__)


def compute_tier(weight: float) -> int:
    thresholds = settings.relationship_tier_thresholds  # [5, 2, 1]
    if weight >= thresholds[0]:
        return 1
    if weight >= thresholds[1]:
        return 2
    return 3


async def build_coauthor_relationships(db: AsyncSession):
    """Build co-author relationships from shared papers."""
    # Get all researcher-paper links
    result = await db.execute(select(researcher_paper))
    links = result.fetchall()

    # Build paper -> set of researcher IDs
    paper_authors: dict[int, set[int]] = defaultdict(set)
    for researcher_id, paper_id in links:
        paper_authors[paper_id].add(researcher_id)

    # Count co-authored papers for each pair
    pair_counts: dict[tuple[int, int], int] = defaultdict(int)
    for paper_id, author_ids in paper_authors.items():
        authors = sorted(author_ids)
        for i in range(len(authors)):
            for j in range(i + 1, len(authors)):
                pair_counts[(authors[i], authors[j])] += 1

    logger.info(f"Found {len(pair_counts)} co-author pairs")

    # Upsert relationships
    for (a_id, b_id), count in pair_counts.items():
        tier = compute_tier(count)

        result = await db.execute(
            select(Relationship).where(
                Relationship.researcher_a_id == a_id,
                Relationship.researcher_b_id == b_id,
                Relationship.type == RelationshipType.co_author,
            )
        )
        rel = result.scalar_one_or_none()

        if rel:
            rel.weight = float(count)
            rel.tier = tier
            rel.last_verified_at = datetime.utcnow()
        else:
            rel = Relationship(
                researcher_a_id=a_id,
                researcher_b_id=b_id,
                type=RelationshipType.co_author,
                tier=tier,
                weight=float(count),
            )
            db.add(rel)

    await db.flush()


async def build_institution_relationships(db: AsyncSession):
    """Build same-institution relationships."""
    result = await db.execute(
        select(Researcher).where(Researcher.affiliation_id.isnot(None))
    )
    researchers = result.scalars().all()

    by_institution: dict[int, list[int]] = defaultdict(list)
    for r in researchers:
        by_institution[r.affiliation_id].append(r.id)

    for inst_id, researcher_ids in by_institution.items():
        ids = sorted(researcher_ids)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                result = await db.execute(
                    select(Relationship).where(
                        Relationship.researcher_a_id == ids[i],
                        Relationship.researcher_b_id == ids[j],
                        Relationship.type == RelationshipType.same_institution,
                    )
                )
                if not result.scalar_one_or_none():
                    db.add(Relationship(
                        researcher_a_id=ids[i],
                        researcher_b_id=ids[j],
                        type=RelationshipType.same_institution,
                        tier=2,
                        weight=1.0,
                    ))

    await db.flush()
