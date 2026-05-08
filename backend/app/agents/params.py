from __future__ import annotations

import re


def extract_year(question: str, default: int = 2025) -> int:
    for m in re.finditer(r"\b(20\d{2})\b", question):
        return int(m.group(1))
    return default


def extract_compare_titles(question: str) -> tuple[str, str] | None:
    m = re.search(r"compare\s+(.+?)\s+vs\.?\s+(.+?)(?:\?|$)", question, re.I | re.DOTALL)
    if m:
        return m.group(1).strip().strip("'\""), m.group(2).strip().strip("'\"")
    m = re.search(r"(.+?)\s+vs\.?\s+(.+?)(?:\?|$)", question, re.I | re.DOTALL)
    if m and len(m.group(1)) < 80 and len(m.group(2)) < 80:
        return m.group(1).strip().strip("'\""), m.group(2).strip().strip("'\"")
    return None


def extract_trend_title(question: str) -> str | None:
    m = re.search(r"why\s+is\s+(.+?)\s+trending", question, re.I | re.DOTALL)
    if m:
        return m.group(1).strip().strip("?.'\"")
    m = re.search(r"trending\s+.*?\b(?:for|with)\s+(.+?)(?:\?|$)", question, re.I)
    if m:
        return m.group(1).strip().strip("?.'\"")
    return None
