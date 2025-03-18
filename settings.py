from cat.mad_hatter.decorators import plugin
from pydantic import BaseModel, Field
from enum import Enum


@plugin
def settings_model():
    class SearchDepth(str, Enum):
        basic = "basic"
        advanced = "advanced"

    class TavilySearchSettings(BaseModel):
        tavily_api_key: str = Field(
            title="Tavily API Key",
            default="",
            description="Your Tavily API key. Get one at https://tavily.com",
        )
        max_results: int = Field(
            title="Max Results Retrieved",
            default=5,
            ge=1,
            description="Default number of search results to return",
        )
        search_depth: SearchDepth = Field(
            title="Search Depth",
            default=SearchDepth.basic,
            description="Default search depth: 'basic' (faster) or 'advanced' (more detailed)",
        )
        include_images: bool = Field(
            title="Include Images",
            default=False,
            description="Whether to include images in the search results",
        )
        include_answer: bool = Field(
            title="Include Answer",
            default=False,
            description="Whether to include an AI-generated answer based on the search results",
        )

    return TavilySearchSettings
