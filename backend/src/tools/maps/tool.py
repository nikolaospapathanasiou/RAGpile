from typing import List, Type

import aiohttp
from pydantic import BaseModel

from tools.base import AsyncBaseTool

from .client import MapsClient, Place


class PlaceSearchInput(BaseModel):
    query: str
    radius: float = 5000


class GoogleMapsPlacesSearchTool(AsyncBaseTool):
    name: str = "google_maps_places_search"
    description: str = (
        "Search for places using Google Maps Places API. Can find businesses, landmarks, and locations."
        "You can assume that the tool knows about the location of the user and you only need to optionally provide a radius in meters."
    )
    args_schema: Type[BaseModel] = PlaceSearchInput

    async def _arun(self, query: str, radius: float = 5000.0, **_kwargs) -> List[Place]:
        async with aiohttp.ClientSession() as session:
            client = MapsClient(
                session=session, api_key=self.dependencies.google_search_api_key
            )
            return await client.text_search(
                query=query,
                location=(52.35102, 4.840184),
                radius=radius,
            )
