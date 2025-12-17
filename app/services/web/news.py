from app.services.web.serpapi_client import fetch_from_api, SerpAPIError
from typing import Dict, List
import re

class NewsAPIError(Exception):
    pass


def fetch_news(params: dict) -> dict:
    try:
        return fetch_from_api(engine="google_news_light", params=params)
    except SerpAPIError as e:
        raise NewsAPIError(str(e)) from e


def format_news_result(
    result: Dict,
    max_days: int = 2,
) -> List[Dict[str, str]]:

    news_results = result.get("news_results", [])
    filtered_news = []

    for item in news_results:
        date_str = item.get("date", "").lower()

        if re.search(r"\b\d+\s+(minute|minutes|min|mins|hour|hours)\b", date_str):
            filtered_news.append(
                {
                    "headline": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                }
            )
            continue

        match = re.search(r"\b(\d+)\s+day", date_str)
        if match:
            days_ago = int(match.group(1))
            if days_ago <= max_days:
                filtered_news.append(
                    {
                        "headline": item.get("title", ""),
                        "snippet": item.get("snippet", ""),
                    }
                )

    return filtered_news
