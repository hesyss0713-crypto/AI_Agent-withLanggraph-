import os
from typing import Iterable

from serpapi import GoogleSearch


class SerpAPIError(Exception):
    pass


def fetch_from_api(
    *,
    engine: str,
    params: dict,
    required_params: Iterable[str] = (),
    api_key_env: str = "SERPAPI_KEY",
) -> dict:
    api_key = os.environ.get(api_key_env)
    if not api_key:
        raise SerpAPIError(f"{api_key_env} is not set")

    merged = {
        "engine": engine,
        **{k: v for k, v in (params or {}).items() if v is not None},
        "api_key": api_key,
    }

    missing = [k for k in required_params if not merged.get(k)]
    if missing:
        raise SerpAPIError(f"Missing required parameter(s): {', '.join(missing)}")

    search = GoogleSearch(merged)
    return search.get_dict()
