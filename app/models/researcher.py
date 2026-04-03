from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Researcher(Base):
    __tablename__ = "researchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    semantic_scholar_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, nullable=False, index=True)
    name_zh = Column(String, nullable=True)
    affiliation_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    h_index = Column(Integer, default=0)
    citation_count = Column(Integer, default=0)
    paper_count = Column(Integer, default=0)
    research_areas = Column(JSON, default=list)
    homepage_url = Column(String, nullable=True)
    last_updated_at = Column(DateTime, default=datetime.utcnow)

    affiliation = relationship("Institution", backref="researchers")
    papers = relationship("Paper", secondary="researcher_paper", back_populates="authors")
