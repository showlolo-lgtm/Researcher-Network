from sqlalchemy import JSON, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.database import Base

researcher_paper = Table(
    "researcher_paper",
    Base.metadata,
    Column("researcher_id", Integer, ForeignKey("researchers.id"), primary_key=True),
    Column("paper_id", Integer, ForeignKey("papers.id"), primary_key=True),
)


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semantic_scholar_id = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=False)
    year = Column(Integer, nullable=True, index=True)
    venue = Column(String, nullable=True)
    citation_count = Column(Integer, default=0)
    abstract = Column(String, nullable=True)
    fields_of_study = Column(JSON, default=list)

    authors = relationship("Researcher", secondary=researcher_paper, back_populates="papers")
