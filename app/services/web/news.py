from app.services.web.serpapi_client import fetch_from_api, SerpAPIError
from typing import Dict, List
import re

class NewsAPIError(Exception):
    pass


def fetch_news(params: dict) -> dict:
    try:
        return fetch_from_api(engine="google_news", params=params)
    except SerpAPIError as e:
        raise NewsAPIError(str(e)) from e


def format_news_result(
    result: Dict,
    min_days: int = 1,
    max_days: int = 3,
) -> List[Dict[str, str]]:

    news_results = result.get("news_results", [])
    filtered_news = []

    for item in news_results:
        date_str = item.get("date", "").lower()

        # "X day ago" 패턴 파싱
        match = re.search(r"(\d+)\s+day", date_str)
        if not match:
            continue

        days_ago = int(match.group(1))

        if min_days <= days_ago <= max_days:
            filtered_news.append({
                "headline": item.get("title", ""),
                "snippet": item.get("snippet", ""),
            })

    return filtered_news