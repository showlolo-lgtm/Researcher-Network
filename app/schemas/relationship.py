from pydantic import BaseModel


class RelationshipOut(BaseModel):
    id: int
    researcher_a_id: int
    researcher_b_id: int
    type: str
    tier: int
    weight: float

    model_config = {"from_attributes": True}
