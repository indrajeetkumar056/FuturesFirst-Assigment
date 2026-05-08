from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from app.agents.params import extract_compare_titles, extract_trend_title, extract_year
from app.agents.router import plan_query
from app.memory_store import DemoStore
from app.schemas.chat import DocumentCitation, ToolTrace
from app.services import analytics
from app.services.retrieval import search_docs_hybrid


@dataclass
class OrchestratorResult:
    tool_trace: list[ToolTrace] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    sql_tables_used: list[str] = field(default_factory=list)
    citations: list[DocumentCitation] = field(default_factory=list)
    context_blocks: list[str] = field(default_factory=list)
    chart: dict | None = None
    route_kind: str | None = None


def _pick_chart(tool_name: str, payload: object) -> dict | None:
    if tool_name == "query_movie_performance" and isinstance(payload, list) and payload:
        return {
            "type": "bar",
            "title": "Top titles by minutes watched",
            "data": payload,
        }
    if tool_name == "get_regional_engagement" and isinstance(payload, list) and payload:
        return {
            "type": "bar",
            "title": "City engagement (last 30 days in data)",
            "data": payload,
        }
    if tool_name == "average_rating_by_genre" and isinstance(payload, list) and payload:
        return {
            "type": "bar",
            "title": "Average rating by genre",
            "data": payload,
        }
    if tool_name == "analyze_genre_growth" and isinstance(payload, list) and payload:
        return {
            "type": "bar",
            "title": "Genre growth (watch minutes)",
            "data": payload,
        }
    if tool_name == "get_audience_insights" and isinstance(payload, list) and payload:
        return {
            "type": "bar",
            "title": "Audience segments by total minutes",
            "data": payload,
        }
    return None


async def run_tool_plan(store: DemoStore, *, question: str) -> OrchestratorResult:
    plan = plan_query(question)
    out = OrchestratorResult(route_kind=plan.route_kind.value)
    year = extract_year(question)
    chart: dict | None = None

    for tool_name in plan.tool_names:
        if tool_name == "retrieve_campaign_documents":
            hits = await search_docs_hybrid(store, query=question, limit=5)
            for h in hits:
                ch = h.chunk
                excerpt = ch.content[:500] + ("…" if len(ch.content) > 500 else "")
                out.citations.append(
                    DocumentCitation(
                        chunk_id=ch.id,
                        source_name=ch.source_name,
                        page_number=ch.page_number,
                        section=ch.section,
                        score=float(h.score),
                        excerpt=excerpt,
                    )
                )
                out.sources.append(f"pdf:{ch.source_name}#p{ch.page_number or '?'}")
            out.context_blocks.append(
                "Retrieved document excerpts:\n"
                + "\n".join(f"[{c.chunk_id} p.{c.page_number}] {c.excerpt}" for c in out.citations[-5:])
            )
            out.tool_trace.append(
                ToolTrace(
                    name="retrieve_campaign_documents",
                    input={"query": question, "limit": 5},
                    output_summary=f"{len(hits)} chunks (hybrid + rerank)",
                )
            )

        elif tool_name == "query_movie_performance":
            rows = analytics.top_titles_by_minutes(store, year=year, limit=8)
            out.sql_tables_used.extend(["movies", "watch_activity"])
            out.sources.append(f"sql:movies,watch_activity year={year}")
            out.context_blocks.append(f"Top titles by minutes ({year}): {rows!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="query_movie_performance",
                    input={"year": year, "limit": 8},
                    output_summary=f"{len(rows)} rows",
                )
            )
            c = _pick_chart("query_movie_performance", rows)
            if c:
                chart = c

        elif tool_name == "get_regional_engagement":
            rows = analytics.city_engagement_last_month(store, limit=12)
            out.sql_tables_used.append("regional_performance")
            out.sources.append("sql:regional_performance")
            out.context_blocks.append(f"Regional engagement: {rows!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="get_regional_engagement",
                    input={"limit": 12},
                    output_summary=f"{len(rows)} rows",
                )
            )
            c = _pick_chart("get_regional_engagement", rows)
            if c:
                chart = c

        elif tool_name == "compare_titles":
            pair = extract_compare_titles(question)
            if pair:
                ta, tb = pair
                payload = analytics.compare_titles(store, title_a=ta, title_b=tb)
                out.sql_tables_used.extend(["movies", "watch_activity", "reviews"])
                out.sources.append("sql:movies,watch_activity,reviews")
                out.context_blocks.append(f"Title comparison: {payload!s}")
                out.tool_trace.append(
                    ToolTrace(
                        name="compare_titles",
                        input={"title_a": ta, "title_b": tb},
                        output_summary="compare_titles",
                    )
                )

        elif tool_name == "title_trend_analysis":
            title = extract_trend_title(question) or "Stellar Run"
            trend = analytics.title_watch_minutes_recent(store, title_substring=title, days_recent=90)
            out.sql_tables_used.extend(["movies", "watch_activity"])
            out.sources.append("sql:movies,watch_activity")
            out.context_blocks.append(f"Title trend window: {trend!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="title_trend_analysis",
                    input={"title_substring": title, "days_recent": 90},
                    output_summary="minutes recent vs prior",
                )
            )

        elif tool_name == "analyze_genre_growth":
            rows = analytics.genre_growth_monthly(store, year=year, limit_months=24)
            out.sql_tables_used.extend(["movies", "watch_activity"])
            out.sources.append(f"sql:movies,watch_activity genre_timeseries year={year}")

            totals: dict[str, float] = defaultdict(float)
            for r in rows:
                totals[str(r.get("genre", ""))] += float(r.get("minutes", 0) or 0)
            bar_rows = [
                {"genre": g, "minutes": round(v, 2)}
                for g, v in sorted(totals.items(), key=lambda x: -x[1])[:12]
            ]
            out.context_blocks.append(f"Genre watch totals ({year}): {bar_rows!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="analyze_genre_growth",
                    input={"year": year},
                    output_summary=f"{len(rows)} time-series points aggregated to {len(bar_rows)} genres",
                )
            )
            c = _pick_chart("query_movie_performance", bar_rows)
            if c:
                c = {**c, "title": f"Genre watch volume ({year})", "data": bar_rows}
                chart = c

        elif tool_name == "average_rating_by_genre":
            rows = analytics.average_rating_by_genre(store, limit=12)
            out.sql_tables_used.extend(["movies", "reviews"])
            out.sources.append("sql:movies,reviews")
            out.context_blocks.append(f"Avg rating by genre: {rows!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="average_rating_by_genre",
                    input={"limit": 12},
                    output_summary=f"{len(rows)} rows",
                )
            )
            c = _pick_chart("average_rating_by_genre", rows)
            if c:
                chart = c

        elif tool_name == "get_audience_insights":
            rows = analytics.audience_segment_engagement(store, limit=12)
            out.sql_tables_used.extend(["viewers", "watch_activity"])
            out.sources.append("sql:viewers,watch_activity")
            out.context_blocks.append(f"Audience segments: {rows!s}")
            out.tool_trace.append(
                ToolTrace(
                    name="get_audience_insights",
                    input={"limit": 12},
                    output_summary=f"{len(rows)} rows",
                )
            )
            c = _pick_chart("get_audience_insights", rows)
            if c:
                chart = c

    out.chart = chart
    if chart:
        out.tool_trace.append(
            ToolTrace(
                name="generate_chart_data",
                input={"chart_type": chart.get("type"), "title": chart.get("title")},
                output_summary="Structured chart payload for UI",
            )
        )
    out.sources = sorted(set(out.sources))
    out.sql_tables_used = sorted(set(out.sql_tables_used))
    return out
