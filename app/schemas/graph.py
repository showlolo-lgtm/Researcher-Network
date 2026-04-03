from pydantic import BaseModel


class GraphNode(BaseModel):
    id: int
    name: str
    affiliation: str | None = None
    h_index: int = 0
    citation_count: int = 0
    research_areas: list[str] = []
    institution_type: str | None = None


class GraphLink(BaseModel):
    source: int
    target: int
    type: str
    tier: int
    weight: float


class GraphData(BaseModel):
    nodes: list[GraphNode]
    links: list[GraphLink]
