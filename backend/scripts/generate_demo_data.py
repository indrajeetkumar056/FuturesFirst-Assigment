from __future__ import annotations

import csv
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path


@dataclass(frozen=True)
class MovieRow:
    title: str
    release_year: int
    genre: str


def _rand_date(start: datetime, end: datetime) -> datetime:
    delta = end - start
    sec = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=sec)


def main() -> None:
    random.seed(7)
    out_dir = Path(__file__).resolve().parent.parent / "demo_data"
    out_dir.mkdir(parents=True, exist_ok=True)

    genres = ["Sci-Fi", "Drama", "Comedy", "Action", "Thriller", "Romance", "Animation", "Fantasy"]
    cities = [
        "Mumbai",
        "Delhi",
        "Bengaluru",
        "London",
        "New York",
        "Los Angeles",
        "Tokyo",
        "Sydney",
        "Berlin",
        "Toronto",
    ]
    segments = ["Family", "Gen Z", "Millennials", "Premium", "Casual", "Sports fans"]

    # Movies
    movies: list[MovieRow] = [
        MovieRow("Stellar Run", 2025, "Sci-Fi"),
        MovieRow("Dark Orbit", 2025, "Sci-Fi"),
        MovieRow("Last Kingdom", 2025, "Drama"),
        MovieRow("Laugh Riot", 2025, "Comedy"),
        MovieRow("Neon Chase", 2024, "Action"),
        MovieRow("Heart Signals", 2024, "Romance"),
        MovieRow("Midnight Clue", 2025, "Thriller"),
        MovieRow("Cloud Canvas", 2025, "Animation"),
    ]
    while len(movies) < 40:
        g = random.choice(genres)
        movies.append(MovieRow(f"{g} Tale {len(movies)+1}", random.choice([2023, 2024, 2025]), g))

    movies_path = out_dir / "movies.csv"
    with movies_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "release_year", "genre"])
        w.writeheader()
        for m in movies:
            w.writerow({"title": m.title, "release_year": m.release_year, "genre": m.genre})

    # Viewers (1000+)
    viewers_path = out_dir / "viewers.csv"
    viewers = []
    with viewers_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["city", "segment"])
        w.writeheader()
        for _ in range(1200):
            row = {"city": random.choice(cities), "segment": random.choice(segments)}
            viewers.append(row)
            w.writerow(row)

    # Watch activity (5000+)
    watch_path = out_dir / "watch_activity.csv"
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 12, 31, tzinfo=timezone.utc)
    with watch_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["movie_id", "viewer_id", "watched_at", "minutes_watched"])
        w.writeheader()
        for _ in range(6500):
            movie_id = random.randint(1, len(movies))
            viewer_id = random.randint(1, len(viewers))
            ts = _rand_date(start, end).isoformat()
            # bias Stellar Run trending late-year
            if movie_id == 1 and random.random() < 0.6:
                ts = _rand_date(datetime(2025, 10, 1, tzinfo=timezone.utc), end).isoformat()
            minutes = random.randint(5, 160)
            w.writerow({"movie_id": movie_id, "viewer_id": viewer_id, "watched_at": ts, "minutes_watched": minutes})

    # Reviews
    reviews_path = out_dir / "reviews.csv"
    with reviews_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["movie_id", "rating", "review_text"])
        w.writeheader()
        for _ in range(1200):
            movie_id = random.randint(1, len(movies))
            # Make comedy slightly weaker to support “weak comedy performance”
            base = 3.0
            if movies[movie_id - 1].genre == "Comedy":
                base = 2.6
            rating = max(1.0, min(5.0, random.gauss(base, 0.7)))
            text = random.choice(
                [
                    "Strong pacing and great cast.",
                    "Enjoyable but some scenes felt slow.",
                    "Loved the visuals and soundtrack.",
                    "Plot was predictable, still fun.",
                    "Would recommend to friends.",
                ]
            )
            w.writerow({"movie_id": movie_id, "rating": round(rating, 1), "review_text": text})

    # Marketing spend
    ms_path = out_dir / "marketing_spend.csv"
    with ms_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["title", "date", "spend_usd"])
        w.writeheader()
        for _ in range(300):
            title = random.choice(movies).title
            date = _rand_date(datetime(2025, 1, 1, tzinfo=timezone.utc), end).date().isoformat()
            spend = max(1_000.0, random.gauss(50_000.0, 25_000.0))
            w.writerow({"title": title, "date": date, "spend_usd": round(spend, 2)})

    # Regional performance
    rp_path = out_dir / "regional_performance.csv"
    with rp_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["city", "date", "engagement_score"])
        w.writeheader()
        for _ in range(600):
            city = random.choice(cities)
            date = _rand_date(datetime(2025, 8, 1, tzinfo=timezone.utc), end).date().isoformat()
            # bias Mumbai strong engagement
            base = 72.0 if city == "Mumbai" else 60.0
            score = max(0.0, min(100.0, random.gauss(base, 10.0)))
            w.writerow({"city": city, "date": date, "engagement_score": round(score, 2)})

    print(f"Wrote demo CSVs to: {out_dir}")


if __name__ == "__main__":
    main()

