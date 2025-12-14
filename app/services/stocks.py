import os
from serpapi import GoogleSearch

class StockAPIError(Exception):
    pass

def fetch_stocks(params: dict):
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        raise StockAPIError("SERPAPI_KEY is not set")

    merged = {
        "engine": "google_finance",
        **{k: v for k, v in params.items() if v is not None},
        "api_key": api_key,
    }
    if "q" not in merged or not merged["q"]:
        raise StockAPIError("Missing required parameter: q")

    search = GoogleSearch(merged)
    return search.get_dict()
