from pydantic import BaseModel


class InstitutionOut(BaseModel):
    id: int
    name: str
    type: str
    country: str = "China"
    city: str | None = None

    model_config = {"from_attributes": True}
