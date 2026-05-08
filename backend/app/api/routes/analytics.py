from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_principal, get_store
from app.core.security import Principal
from app.memory_store import DemoStore
from app.services import analytics as an

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/top-titles")
def top_titles(
    year: int = Query(2025, ge=1900, le=2100),
    limit: int = Query(5, ge=1, le=50),
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    return {"year": year, "rows": an.top_titles_by_minutes(store, year=year, limit=limit)}


@router.get("/city-engagement")
def city_engagement(
    limit: int = Query(10, ge=1, le=100),
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    return {"rows": an.city_engagement_last_month(store, limit=limit)}


@router.get("/rating-by-genre")
def rating_by_genre(
    limit: int = Query(10, ge=1, le=100),
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    return {"rows": an.average_rating_by_genre(store, limit=limit)}


@router.get("/genre-growth")
def genre_growth(
    year: Annotated[int | None, Query(ge=1900, le=2100)] = None,
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    rows = an.genre_growth_monthly(store, year=year, limit_months=24)
    return {"rows": rows}


@router.get("/regional-performance")
def regional_performance(
    limit: int = Query(10, ge=1, le=100),
    _principal: Principal = Depends(get_principal),
    store: DemoStore = Depends(get_store),
):
    return {"rows": an.city_engagement_last_month(store, limit=limit)}
