import enum
from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint

from app.database import Base


class RelationshipType(str, enum.Enum):
    co_author = "co_author"
    advisor_advisee = "advisor_advisee"
    same_institution = "same_institution"
    same_alma_mater = "same_alma_mater"


class Relationship(Base):
    __tablename__ = "relationships"
    __table_args__ = (
        UniqueConstraint("researcher_a_id", "researcher_b_id", "type", name="uq_relationship"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    researcher_a_id = Column(Integer, ForeignKey("researchers.id"), nullable=False, index=True)
    researcher_b_id = Column(Integer, ForeignKey("researchers.id"), nullable=False, index=True)
    type = Column(Enum(RelationshipType), nullable=False)
    tier = Column(Integer, default=3)  # 1=closest, 3=weakest
    weight = Column(Float, default=1.0)  # e.g. number of co-authored papers
    last_verified_at = Column(DateTime, default=datetime.utcnow)
