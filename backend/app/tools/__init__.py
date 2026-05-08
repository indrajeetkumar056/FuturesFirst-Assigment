"""Callable tools used by the agent (wrappers over analytics + RAG)."""

TOOL_NAMES = (
    "retrieve_campaign_documents",
    "query_movie_performance",
    "get_regional_engagement",
    "compare_titles",
    "title_trend_analysis",
    "analyze_genre_growth",
    "average_rating_by_genre",
    "get_audience_insights",
    "generate_chart_data",
)

__all__ = ["TOOL_NAMES"]
