import enum

from sqlalchemy import Column, Enum, Integer, String

from app.database import Base


class InstitutionType(str, enum.Enum):
    university = "university"
    research_institute = "research_institute"
    company = "company"


class Institution(Base):
    __tablename__ = "institutions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)
    type = Column(Enum(InstitutionType), nullable=False)
    country = Column(String, default="China")
    city = Column(String, nullable=True)
