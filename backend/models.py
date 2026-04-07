from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class SeriesMaster(SQLModel, table=True):
    __tablename__ = "series_master"

    series_id: int = Field(primary_key=True)
    level: int
    name: str
    parent_id: Optional[float] = None
    full_path: str


class Observation(SQLModel, table=True):
    __tablename__ = "observations"

    series_id: int = Field(foreign_key="series_master.series_id", primary_key=True)
    month: str = Field(primary_key=True)
    date: datetime = Field(primary_key=True)
    value: float