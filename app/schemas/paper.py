from pydantic import BaseModel


class PaperOut(BaseModel):
    id: int
    semantic_scholar_id: str | None = None
    title: str
    year: int | None = None
    venue: str | None = None
    citation_count: int = 0
    fields_of_study: list[str] = []

    model_config = {"from_attributes": True}
