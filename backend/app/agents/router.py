from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from app.agents.params import extract_compare_titles, extract_trend_title


class RouteKind(str, Enum):
    SQL = "sql_analytics"
    DOC = "document_retrieval"
    HYBRID = "hybrid_reasoning"
    RECOMMEND = "recommendation"


@dataclass(frozen=True)
class QueryPlan:
    """Deterministic router output (no LLM raw SQL). Extend with LLM classification later."""

    route_kind: RouteKind
    tool_names: list[str]


def plan_query(question: str) -> QueryPlan:
    q = question.lower()
    tools: list[str] = []

    def add(name: str) -> None:
        if name not in tools:
            tools.append(name)

    is_compare = "compare" in q or " vs " in q or " versus " in q
    is_trend = "trending" in q or "why is" in q or "why did" in q
    is_top = any(
        p in q
        for p in (
            "performed best",
            "best titles",
            "which titles",
            "top title",
            "top movies",
            "best movies",
            "best in 20",
        )
    )
    is_city = "city" in q and ("engagement" in q or "strongest" in q or "regional" in q)
    is_genre = "genre" in q or "comedy" in q or "weak" in q or "growing" in q
    is_audience = any(
        p in q for p in ("audience", "segment", "gen z", "millennials", "premium", "casual")
    )
    is_recommend = any(
        p in q for p in ("recommend", "leadership", "next quarter", "should we", "take next")
    )

    if is_compare and extract_compare_titles(question):
        add("compare_titles")

    if is_trend:
        t = extract_trend_title(question)
        if t:
            add("title_trend_analysis")
        add("retrieve_campaign_documents")

    if is_top:
        add("query_movie_performance")

    if is_city:
        add("get_regional_engagement")

    if is_genre:
        add("analyze_genre_growth")
        add("average_rating_by_genre")

    if is_audience:
        add("get_audience_insights")

    if is_recommend:
        add("retrieve_campaign_documents")
        add("query_movie_performance")
        add("get_audience_insights")
        add("analyze_genre_growth")

    if not tools:
        add("retrieve_campaign_documents")
        add("query_movie_performance")

    if is_recommend:
        kind = RouteKind.RECOMMEND
    elif (is_compare or is_top or is_city or is_genre) and not is_trend and not is_recommend:
        kind = RouteKind.SQL
    elif is_trend and not is_top and not is_city:
        kind = RouteKind.DOC
    else:
        kind = RouteKind.HYBRID

    return QueryPlan(route_kind=kind, tool_names=tools)
