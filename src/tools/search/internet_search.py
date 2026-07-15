import os

from tavily import TavilyClient

from logger import logger, ErrorMessage
from models.tools import ToolParameter
from tools.tool import Tool


class InternetSearch(Tool):

    def __init__(self):
        self._api_key = os.environ["TAVILY_API_KEY"]

    @property
    def tool_name(self) -> str:
        return "internet_search"

    @property
    def description(self) -> str:
        return (
            "Search the internet for up-to-date information on any topic. "
            "Use this when the user asks about recent events, facts, or anything "
            "that may require live web data."
        )

    @property
    def parameters(self) -> list[ToolParameter]:
        return [
            ToolParameter(
                name="query",
                description="The search query to look up on the internet.",
                type="string",
                required=True,
            ),
            ToolParameter(
                name="search_depth",
                description=(
                    "Depth of the search. 'basic' is faster and sufficient for most queries. "
                    "'advanced' performs a deeper search for complex or obscure topics."
                ),
                type="string",
                required=False,
                enum=["basic", "advanced"],
            ),
        ]

    def execute(self, query: str, search_depth: str = "basic") -> str:
        try:
            client = TavilyClient(api_key=self._api_key)
            response = client.search(query=query, search_depth=search_depth)

            results = response.get("results", [])
            if not results:
                return "No results found for the given query."

            formatted_results = []
            for i, result in enumerate(results, start=1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content available.")
                formatted_results.append(
                    f"{i}. {title}\n   URL: {url}\n   {content}"
                )

            return "Internet search results:\n\n" + "\n\n".join(formatted_results)

        except Exception as e:
            logger.log(ErrorMessage(content=f"{self.__class__.__name__} : internet_search: {e}"))
            raise
