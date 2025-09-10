import logging
from dataclasses import dataclass
from typing import Optional

import aiohttp


@dataclass
class Place:
    url: str
    name: str
    rating: Optional[float]
    display_name: str
    primary_type: str
    review_summary: str


FIELDS_TEXT_SEARCH = [
    "places.googleMapsUri",
    "places.name",
    "places.displayName.text",
    "places.primaryType",
    "places.rating",
]

FIELDS_PLACE_DETAILS = ["*"]

logger = logging.getLogger(__name__)


class MapsClient:
    def __init__(self, session: aiohttp.ClientSession, api_key: str):
        self.api_key = api_key
        self.session = session

    async def text_search(
        self, query: str, location: tuple[float, float], radius: float
    ) -> list[Place]:
        res = await self.session.post(
            "https://places.googleapis.com/v1/places:searchText",
            json={
                "textQuery": query,
                "locationBias": {
                    "circle": {
                        "center": {"latitude": location[0], "longitude": location[1]},
                        "radius": radius,
                    }
                },
            },
            headers={
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-fieldMask": ",".join(FIELDS_TEXT_SEARCH),
            },
        )
        payload = await res.json()
        if not res.ok:
            raise ValueError(
                f"Text search failed with status code {res.status} and body {payload}"
            )
        logger.info(payload)
        return [
            Place(
                name=place["name"],
                url=place["googleMapsUri"],
                display_name=place["displayName"]["text"],
                primary_type=place["primaryType"],
                rating=place.get("rating"),
                review_summary="",
            )
            for place in payload["places"]
        ]

    async def place_details(self, place_name: str) -> dict:
        res = await self.session.get(
            f"https://places.googleapis.com/v1/{place_name}",
            headers={
                "X-Goog-Api-Key": self.api_key,
                "X-Goog-fieldMask": ",".join(FIELDS_PLACE_DETAILS),
            },
        )
        payload = await res.json()
        if not res.ok:
            raise ValueError(
                f"Place details failed with status code {res.status} and body {payload}"
            )
        logger.info(payload)
        return payload
