from app.services.web.serpapi_client import fetch_from_api, SerpAPIError


class StockAPIError(Exception):
    pass


def fetch_stocks(params: dict):
    try:
        return fetch_from_api(engine="google_finance", params=params, required_params=("q",))
    except SerpAPIError as e:
        raise StockAPIError(str(e)) from e


def format_stock_result(data: dict) -> str:
    summary = data.get("summary", {}) or {}
    markets = data.get("markets", {}) or {}
    us = markets.get("us", []) or []

    lines = []
    lines.append(f"TODAY: {summary.get('date', 'N/A')}")
    lines.append("")

    for item in us[:5]:
        lines.append(f"NAME: {item.get('name', 'N/A')}")
        lines.append(f"PRICE: ${item.get('price', 'N/A')}")
        lines.append("")

    lines.append("<<< 요청 종목 내용 >>>")
    lines.append(f"TITLE: {summary.get('title', 'N/A')}")
    lines.append(f"STOCK: {summary.get('stock', 'N/A')}")
    lines.append(f"EXCHANGE: {summary.get('exchange', 'N/A')}")
    lines.append(
        f"PRICE: {summary.get('price', 'N/A')}  "
        f"({summary.get('market', {}).get('trading', 'After Hours')}) -> "
        f"{summary.get('market', {}).get('price', 'N/A')}"
    )
    lines.append(
        "PERCENTAGE: "
        f"{summary.get('price_movement', {}).get('percentage', 'N/A')} "
        f"{summary.get('price_movement', {}).get('movement', 'N/A')} "
        f"({summary.get('market', {}).get('trading', 'After Hours')}) -> "
        f"{summary.get('market', {}).get('price_movement', {}).get('percentage', 'N/A')} "
        f"{summary.get('market', {}).get('price_movement', {}).get('movement', 'N/A')}"
    )

    return "\n".join(lines)
