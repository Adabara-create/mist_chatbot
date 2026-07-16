from tavily import TavilyClient

from app.config import settings

_client = TavilyClient(api_key=settings.tavily_api_key)


def web_search(query: str, max_results: int = 5) -> list[dict]:
    response = _client.search(query=query, max_results=max_results)
    return [
        {
            "title": r.get("title"),
            "url": r.get("url"),
            "content": r.get("content"),
        }
        for r in response.get("results", [])
    ]
