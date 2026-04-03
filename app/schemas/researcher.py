from datetime import datetime

from pydantic import BaseModel


class ResearcherBase(BaseModel):
    name: str
    name_zh: str | None = None
    h_index: int = 0
    citation_count: int = 0
    paper_count: int = 0
    research_areas: list[str] = []
    homepage_url: str | None = None


class ResearcherCreate(ResearcherBase):
    semantic_scholar_id: str | None = None
    affiliation_id: int | None = None


class ResearcherOut(ResearcherBase):
    id: int
    semantic_scholar_id: str | None = None
    affiliation_id: int | None = None
    affiliation_name: str | None = None
    last_updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class ResearcherSearch(BaseModel):
    query: str = ""
    institution_id: int | None = None
    research_area: str | None = None
    min_h_index: int | None = None
    limit: int = 50
    offset: int = 0
