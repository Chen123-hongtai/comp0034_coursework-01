from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Session, select
from sqlalchemy import Integer, func

from backend.database import get_session, init_db
from backend.models import Observation, SeriesMaster
from backend.schemas import (
    DashboardSummary,
    HealthResponse,
    MarketMetric,
    MonthlyPoint,
    ObservationCreate,
    ObservationRead,
    ScenarioHistoryPoint,
    ScenarioHistoryResponse,
    SeriesRead,
)

@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Singapore Tourism REST API", version="0.1.0", lifespan=lifespan)


@app.get("/api/v1/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/api/v1/series", response_model=list[SeriesRead])
def list_series(
    level: Optional[int] = Query(default=None, ge=0, le=5),
    session: Session = Depends(get_session),
) -> list[SeriesMaster]:
    statement = select(SeriesMaster)
    if level is not None:
        statement = statement.where(SeriesMaster.level == level)
    statement = statement.order_by(SeriesMaster.level, SeriesMaster.name)
    return list(session.exec(statement))


@app.get("/api/v1/series/{series_id}", response_model=SeriesRead)
def get_series(series_id: int, session: Session = Depends(get_session)) -> SeriesMaster:
    series = session.get(SeriesMaster, series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@app.get("/api/v1/regions", response_model=list[str])
def list_regions(session: Session = Depends(get_session)) -> list[str]:
    rows = session.exec(
        select(SeriesMaster.name)
        .where(SeriesMaster.level == 1)
        .order_by(SeriesMaster.name)
    ).all()
    return list(rows)


@app.get("/api/v1/markets", response_model=list[str])
def list_markets(
    region: Optional[str] = None,
    session: Session = Depends(get_session),
) -> list[str]:
    statement = select(SeriesMaster.name).where(SeriesMaster.level == 2)
    if region:
        region_series = session.exec(
            select(SeriesMaster).where(
                SeriesMaster.level == 1,
                SeriesMaster.name == region,
            )
        ).first()
        if not region_series:
            raise HTTPException(status_code=404, detail="Region not found")
        statement = statement.where(SeriesMaster.parent_id == float(region_series.series_id))

    rows = session.exec(statement.order_by(SeriesMaster.name)).all()
    return list(rows)


@app.get("/api/v1/observations", response_model=list[ObservationRead])
def list_observations(
    series_id: Optional[int] = None,
    limit: int = Query(default=100, ge=1, le=1000),
    session: Session = Depends(get_session),
) -> list[Observation]:
    statement = select(Observation)
    if series_id is not None:
        statement = statement.where(Observation.series_id == series_id)
    statement = statement.order_by(Observation.date.desc()).limit(limit)
    return list(session.exec(statement))


def _get_region_series(session: Session, region: str) -> SeriesMaster:
    record = session.exec(
        select(SeriesMaster).where(SeriesMaster.level == 1, SeriesMaster.name == region)
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Region not found")
    return record


@app.get("/api/v1/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(region: str, session: Session = Depends(get_session)) -> DashboardSummary:
    region_series = _get_region_series(session, region)

    monthly_rows = session.exec(
        select(Observation.date, Observation.value)
        .where(Observation.series_id == region_series.series_id)
        .order_by(Observation.date)
    ).all()
    if not monthly_rows:
        raise HTTPException(status_code=404, detail="No observations found for region")

    latest_date = monthly_rows[-1][0]
    latest_year = int(latest_date.strftime("%Y"))
    latest_month = int(latest_date.strftime("%m"))

    current_ytd = session.exec(
        select(func.sum(Observation.value)).where(
            Observation.series_id == region_series.series_id,
            func.strftime("%Y", Observation.date) == str(latest_year),
            func.cast(func.strftime("%m", Observation.date), Integer) <= latest_month,
        )
    ).one()
    previous_ytd = session.exec(
        select(func.sum(Observation.value)).where(
            Observation.series_id == region_series.series_id,
            func.strftime("%Y", Observation.date) == str(latest_year - 1),
            func.cast(func.strftime("%m", Observation.date), Integer) <= latest_month,
        )
    ).one()

    yoy_growth_pct = None
    if previous_ytd and previous_ytd != 0:
        yoy_growth_pct = ((current_ytd - previous_ytd) / previous_ytd) * 100

    recovery_base = session.exec(
        select(Observation.value).where(
            Observation.series_id == region_series.series_id,
            func.strftime("%Y", Observation.date) == "2019",
            func.strftime("%m", Observation.date) == latest_date.strftime("%m"),
        )
    ).first()

    recovery_rate_pct = None
    latest_value = monthly_rows[-1][1]
    if recovery_base and recovery_base != 0:
        recovery_rate_pct = (latest_value / recovery_base) * 100

    total_visitors = float(current_ytd or 0.0)
    last_24 = monthly_rows[-24:]
    points = [MonthlyPoint(date=row[0], visitors=float(row[1])) for row in last_24]

    return DashboardSummary(
        region=region,
        total_visitors=total_visitors,
        yoy_growth_pct=yoy_growth_pct,
        recovery_rate_pct=recovery_rate_pct,
        monthly_points=points,
    )


@app.get("/api/v1/market-explorer", response_model=list[MarketMetric])
def market_explorer_metrics(session: Session = Depends(get_session)) -> list[MarketMetric]:
    markets = session.exec(
        select(SeriesMaster)
        .where(SeriesMaster.level == 2)
        .order_by(SeriesMaster.parent_id, SeriesMaster.name)
    ).all()

    results: list[MarketMetric] = []

    for market in markets:
        latest_date = session.exec(
            select(func.max(Observation.date)).where(Observation.series_id == market.series_id)
        ).one()
        if not latest_date:
            continue

        latest_year = int(latest_date.strftime("%Y"))
        latest_month = int(latest_date.strftime("%m"))
        current_ytd = session.exec(
            select(func.sum(Observation.value)).where(
                Observation.series_id == market.series_id,
                func.strftime("%Y", Observation.date) == str(latest_year),
                func.cast(func.strftime("%m", Observation.date), Integer) <= latest_month,
            )
        ).one()
        previous_ytd = session.exec(
            select(func.sum(Observation.value)).where(
                Observation.series_id == market.series_id,
                func.strftime("%Y", Observation.date) == str(latest_year - 1),
                func.cast(func.strftime("%m", Observation.date), Integer) <= latest_month,
            )
        ).one()

        yoy_growth_pct = None
        if previous_ytd and previous_ytd != 0:
            yoy_growth_pct = ((current_ytd - previous_ytd) / previous_ytd) * 100

        parent = session.get(SeriesMaster, int(market.parent_id)) if market.parent_id is not None else None
        region_name = parent.name if parent else "Unknown"

        results.append(
            MarketMetric(
                region=region_name,
                market=market.name,
                visitors_ytd=float(current_ytd or 0.0),
                yoy_growth_pct=yoy_growth_pct,
            )
        )

    return results


@app.get("/api/v1/scenario/markets", response_model=list[str])
def scenario_market_options(session: Session = Depends(get_session)) -> list[str]:
    root_series = session.exec(
        select(SeriesMaster.name).where(SeriesMaster.level == 0).order_by(SeriesMaster.name)
    ).all()
    regions = session.exec(
        select(SeriesMaster.name).where(SeriesMaster.level == 1).order_by(SeriesMaster.name)
    ).all()
    options = ["Total Inbound"]
    options.extend(name for name in regions if name not in options)
    options.extend(name for name in root_series if name not in options)
    return options


@app.get("/api/v1/scenario/history", response_model=ScenarioHistoryResponse)
def scenario_history(market: str, session: Session = Depends(get_session)) -> ScenarioHistoryResponse:
    if market == "Total Inbound":
        series = session.exec(select(SeriesMaster).where(SeriesMaster.level == 0)).first()
    else:
        series = session.exec(select(SeriesMaster).where(SeriesMaster.name == market)).first()

    if not series:
        raise HTTPException(status_code=404, detail="Market not found")

    rows = session.exec(
        select(Observation.date, Observation.value)
        .where(Observation.series_id == series.series_id)
        .order_by(Observation.date)
    ).all()

    points = [ScenarioHistoryPoint(date=row[0], visitors=float(row[1])) for row in rows]
    return ScenarioHistoryResponse(market=market, points=points)


@app.post("/api/v1/observations", response_model=ObservationRead, status_code=201)
def create_observation(payload: ObservationCreate, session: Session = Depends(get_session)) -> Observation:
    existing = session.exec(
        select(Observation).where(
            Observation.series_id == payload.series_id,
            Observation.month == payload.month,
            Observation.date == payload.date,
        )
    ).first()
    if existing:
        raise HTTPException(status_code=409, detail="Observation already exists")

    observation = Observation.model_validate(payload)
    session.add(observation)
    session.commit()
    session.refresh(observation)
    return observation


@app.put("/api/v1/observations/{series_id}/{month}", response_model=ObservationRead)
def update_observation(
    series_id: int,
    month: str,
    value: float,
    session: Session = Depends(get_session),
) -> Observation:
    target = session.exec(
        select(Observation)
        .where(Observation.series_id == series_id, Observation.month == month)
        .order_by(Observation.date.desc())
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Observation not found")

    target.value = value
    session.add(target)
    session.commit()
    session.refresh(target)
    return target


@app.delete("/api/v1/observations/{series_id}/{month}")
def delete_observation(series_id: int, month: str, session: Session = Depends(get_session)) -> dict:
    target = session.exec(
        select(Observation)
        .where(Observation.series_id == series_id, Observation.month == month)
        .order_by(Observation.date.desc())
    ).first()
    if not target:
        raise HTTPException(status_code=404, detail="Observation not found")

    session.delete(target)
    session.commit()
    return {"deleted": True}
