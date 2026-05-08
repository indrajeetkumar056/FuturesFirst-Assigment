from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from app.memory_store import DemoStore


def top_titles_by_minutes(store: DemoStore, *, year: int, limit: int = 5) -> list[dict]:
    title_to_minutes: dict[str, float] = defaultdict(float)
    id_to_title = {m["id"]: m["title"] for m in store.movies}
    for w in store.watch_activity:
        if w["watched_at"].year != year:
            continue
        tid = id_to_title.get(w["movie_id"])
        if tid:
            title_to_minutes[tid] += float(w["minutes_watched"])
    rows = [{"title": t, "minutes": v} for t, v in title_to_minutes.items()]
    rows.sort(key=lambda x: -x["minutes"])
    return rows[:limit]


def city_engagement_last_month(store: DemoStore, *, limit: int = 10) -> list[dict]:
    if not store.regional_performance:
        return []
    max_date = max(r["date"] for r in store.regional_performance)
    cutoff = max_date - timedelta(days=30)
    city_vals: dict[str, list[float]] = defaultdict(list)
    for r in store.regional_performance:
        if r["date"] >= cutoff:
            city_vals[r["city"]].append(r["engagement_score"])
    out = [{"city": c, "engagement": sum(v) / len(v)} for c, v in city_vals.items()]
    out.sort(key=lambda x: -x["engagement"])
    return out[:limit]


def average_rating_by_genre(store: DemoStore, *, limit: int = 10) -> list[dict]:
    id_to_genre = {m["id"]: m["genre"] for m in store.movies}
    genre_ratings: dict[str, list[float]] = defaultdict(list)
    for rev in store.reviews:
        g = id_to_genre.get(rev["movie_id"])
        if g:
            genre_ratings[g].append(rev["rating"])
    rows = [{"genre": g, "rating": sum(rs) / len(rs)} for g, rs in genre_ratings.items()]
    rows.sort(key=lambda x: -x["rating"])
    return rows[:limit]


def title_watch_minutes_recent(
    store: DemoStore,
    *,
    title_substring: str,
    days_recent: int = 90,
) -> dict:
    sub = title_substring.lower()
    matching_ids = {m["id"] for m in store.movies if sub in m["title"].lower()}
    times = [w["watched_at"] for w in store.watch_activity if w["movie_id"] in matching_ids]
    if not times:
        return {"title_match": title_substring, "recent_minutes": 0.0, "prior_minutes": 0.0}
    end = max(times)
    recent_start = end - timedelta(days=days_recent)
    prior_start = end - timedelta(days=days_recent * 2)
    prior_end = recent_start
    recent = sum(
        w["minutes_watched"]
        for w in store.watch_activity
        if w["movie_id"] in matching_ids and recent_start <= w["watched_at"] <= end
    )
    prior = sum(
        w["minutes_watched"]
        for w in store.watch_activity
        if w["movie_id"] in matching_ids and prior_start <= w["watched_at"] < prior_end
    )
    return {
        "title_match": title_substring,
        "recent_minutes": float(recent),
        "prior_minutes": float(prior),
        "recent_window_days": days_recent,
    }


def compare_titles(store: DemoStore, *, title_a: str, title_b: str) -> dict:
    def _one(title_sub: str) -> dict:
        sub = title_sub.lower()
        movie = next((m for m in store.movies if sub in m["title"].lower()), None)
        if not movie:
            return {"title_query": title_sub, "found": False}
        mid = movie["id"]
        minutes = sum(w["minutes_watched"] for w in store.watch_activity if w["movie_id"] == mid)
        ratings = [r["rating"] for r in store.reviews if r["movie_id"] == mid]
        rating = sum(ratings) / len(ratings) if ratings else 0.0
        return {
            "title": movie["title"],
            "genre": movie["genre"],
            "release_year": movie["release_year"],
            "total_minutes_watched": float(minutes),
            "avg_review_rating": round(rating, 2),
            "found": True,
        }

    return {"title_a": _one(title_a), "title_b": _one(title_b)}


def genre_growth_monthly(
    store: DemoStore,
    *,
    year: int | None = None,
    limit_months: int = 24,
) -> list[dict]:
    by_key: dict[tuple[str, str], float] = defaultdict(float)
    id_to_genre = {m["id"]: m["genre"] for m in store.movies}
    for w in store.watch_activity:
        if year is not None and w["watched_at"].year != year:
            continue
        g = id_to_genre.get(w["movie_id"])
        if not g:
            continue
        month_key = w["watched_at"].strftime("%Y-%m-01")
        by_key[(g, month_key)] += float(w["minutes_watched"])
    rows = [{"genre": g, "month": m, "minutes": v} for (g, m), v in sorted(by_key.items())]
    cap = limit_months * 10
    return rows[-cap:] if len(rows) > cap else rows


def audience_segment_engagement(store: DemoStore, *, limit: int = 15) -> list[dict]:
    id_to_segment = {v["id"]: v["segment"] for v in store.viewers}
    seg_minutes: dict[str, float] = defaultdict(float)
    seg_viewers: dict[str, set[int]] = defaultdict(set)
    for w in store.watch_activity:
        seg = id_to_segment.get(w["viewer_id"])
        if seg:
            seg_minutes[seg] += float(w["minutes_watched"])
            seg_viewers[seg].add(w["viewer_id"])
    rows = [
        {"segment": s, "total_minutes": seg_minutes[s], "unique_viewers": len(seg_viewers[s])}
        for s in seg_minutes
    ]
    rows.sort(key=lambda x: -x["total_minutes"])
    return rows[:limit]
