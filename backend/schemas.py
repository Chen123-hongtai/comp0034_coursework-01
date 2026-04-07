from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class SeriesRead(BaseModel):
    series_id: int
    level: int
    name: str
    parent_id: Optional[float]
    full_path: str


class ObservationRead(BaseModel):
    series_id: int
    month: str
    date: datetime
    value: float


class ObservationCreate(BaseModel):
    series_id: int
    month: str
    date: datetime
    value: float


class MonthlyPoint(BaseModel):
    date: datetime
    visitors: float


class DashboardSummary(BaseModel):
    region: str
    total_visitors: float
    yoy_growth_pct: Optional[float]
    recovery_rate_pct: Optional[float]
    monthly_points: list[MonthlyPoint]


class MarketMetric(BaseModel):
    region: str
    market: str
    visitors_ytd: float
    yoy_growth_pct: Optional[float]


class ScenarioHistoryPoint(BaseModel):
    date: datetime
    visitors: float


class ScenarioHistoryResponse(BaseModel):
    market: str
    points: list[ScenarioHistoryPoint]