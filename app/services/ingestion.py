import json
import logging
from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.institution import Institution
from app.models.paper import Paper, researcher_paper
from app.models.researcher import Researcher
from app.services.relationship_builder import build_coauthor_relationships
from app.services.semantic_scholar import s2_client

logger = logging.getLogger(__name__)

SEED_FILE = Path(__file__).parent.parent / "seed" / "researchers.json"


async def load_seed_data() -> list[dict]:
    with open(SEED_FILE) as f:
        return json.load(f)


async def resolve_author(entry: dict) -> dict | None:
    """Resolve a seed entry to an S2 author profile."""
    if entry.get("semantic_scholar_id"):
        return await s2_client.get_author(entry["semantic_scholar_id"])

    results = await s2_client.search_author(entry["name"])
    if not results:
        logger.warning(f"No S2 results for: {entry['name']}")
        return None

    # Try to match by affiliation hint
    hint = entry.get("affiliation_hint", "").lower()
    for r in results:
        affiliations = " ".join(r.get("affiliations", [])).lower()
        if hint and hint in affiliations:
            return r

    return results[0]  # Fall back to top result


async def upsert_institution(db: AsyncSession, name: str, inst_type: str) -> Institution:
    result = await db.execute(select(Institution).where(Institution.name == name))
    inst = result.scalar_one_or_none()
    if not inst:
        inst = Institution(name=name, type=inst_type)
        db.add(inst)
        await db.flush()
    return inst


async def upsert_researcher(db: AsyncSession, author_data: dict, affiliation_id: int | None) -> Researcher:
    s2_id = author_data.get("authorId")
    result = await db.execute(
        select(Researcher).where(Researcher.semantic_scholar_id == s2_id)
    )
    researcher = result.scalar_one_or_none()

    if researcher:
        researcher.h_index = author_data.get("hIndex", 0) or 0
        researcher.citation_count = author_data.get("citationCount", 0) or 0
        researcher.paper_count = author_data.get("paperCount", 0) or 0
        researcher.last_updated_at = datetime.utcnow()
    else:
        researcher = Researcher(
            semantic_scholar_id=s2_id,
            name=author_data.get("name", ""),
            affiliation_id=affiliation_id,
            h_index=author_data.get("hIndex", 0) or 0,
            citation_count=author_data.get("citationCount", 0) or 0,
            paper_count=author_data.get("paperCount", 0) or 0,
            homepage_url=author_data.get("homepage"),
            research_areas=[],
        )
        db.add(researcher)
        await db.flush()

    return researcher


async def upsert_paper(db: AsyncSession, paper_data: dict) -> Paper | None:
    s2_id = paper_data.get("paperId")
    if not s2_id:
        return None

    result = await db.execute(select(Paper).where(Paper.semantic_scholar_id == s2_id))
    paper = result.scalar_one_or_none()

    if paper:
        paper.citation_count = paper_data.get("citationCount", 0) or 0
    else:
        paper = Paper(
            semantic_scholar_id=s2_id,
            title=paper_data.get("title", ""),
            year=paper_data.get("year"),
            venue=paper_data.get("venue"),
            citation_count=paper_data.get("citationCount", 0) or 0,
            abstract=paper_data.get("abstract"),
            fields_of_study=paper_data.get("fieldsOfStudy") or [],
        )
        db.add(paper)
        await db.flush()

    return paper


async def ingest_researcher(db: AsyncSession, entry: dict) -> Researcher | None:
    """Ingest a single researcher from seed data."""
    author_data = await resolve_author(entry)
    if not author_data:
        return None

    # Resolve institution
    affiliation_id = None
    affiliations = author_data.get("affiliations", [])
    if affiliations:
        inst = await upsert_institution(db, affiliations[0], entry.get("institution_type", "university"))
        affiliation_id = inst.id

    researcher = await upsert_researcher(db, author_data, affiliation_id)

    # Fetch and link papers (top 50 by citation)
    papers_data = await s2_client.get_author_papers(author_data["authorId"], limit=50)
    research_areas = set()

    for p_data in papers_data:
        paper = await upsert_paper(db, p_data)
        if paper:
            # Link researcher to paper
            exists = await db.execute(
                select(researcher_paper).where(
                    researcher_paper.c.researcher_id == researcher.id,
                    researcher_paper.c.paper_id == paper.id,
                )
            )
            if not exists.first():
                await db.execute(
                    researcher_paper.insert().values(
                        researcher_id=researcher.id, paper_id=paper.id
                    )
                )

            for field in p_data.get("fieldsOfStudy") or []:
                research_areas.add(field)

            # Also upsert co-authors as lightweight researcher records
            for coauthor in p_data.get("authors", []):
                if coauthor.get("authorId") and coauthor["authorId"] != author_data["authorId"]:
                    co_res = await upsert_researcher(
                        db,
                        {"authorId": coauthor["authorId"], "name": coauthor.get("name", "")},
                        None,
                    )
                    exists2 = await db.execute(
                        select(researcher_paper).where(
                            researcher_paper.c.researcher_id == co_res.id,
                            researcher_paper.c.paper_id == paper.id,
                        )
                    )
                    if not exists2.first():
                        await db.execute(
                            researcher_paper.insert().values(
                                researcher_id=co_res.id, paper_id=paper.id
                            )
                        )

    researcher.research_areas = list(research_areas)
    await db.flush()

    return researcher


async def run_seed_ingestion(db: AsyncSession):
    """Run full seed ingestion pipeline."""
    seed_data = await load_seed_data()
    logger.info(f"Starting ingestion of {len(seed_data)} seed researchers")

    for i, entry in enumerate(seed_data):
        try:
            researcher = await ingest_researcher(db, entry)
            if researcher:
                logger.info(f"[{i+1}/{len(seed_data)}] Ingested: {researcher.name}")
            else:
                logger.warning(f"[{i+1}/{len(seed_data)}] Failed: {entry['name']}")
        except Exception as e:
            logger.error(f"[{i+1}/{len(seed_data)}] Error for {entry['name']}: {e}")

    # Build relationships after all researchers are ingested
    await build_coauthor_relationships(db)
    await db.commit()
    logger.info("Seed ingestion complete")


async def run_refresh(db: AsyncSession):
    """Refresh stale researcher data."""
    from datetime import timedelta

    cutoff = datetime.utcnow() - timedelta(days=7)
    result = await db.execute(
        select(Researcher).where(Researcher.last_updated_at < cutoff).limit(100)
    )
    stale = result.scalars().all()
    logger.info(f"Refreshing {len(stale)} stale researchers")

    for researcher in stale:
        if researcher.semantic_scholar_id:
            entry = {
                "name": researcher.name,
                "semantic_scholar_id": researcher.semantic_scholar_id,
            }
            await ingest_researcher(db, entry)

    await build_coauthor_relationships(db)
    await db.commit()
