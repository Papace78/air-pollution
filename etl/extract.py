"""Handles data extraction from OpenAQ API and returns JSON responses."""

import os

from dotenv import load_dotenv
import httpx

load_dotenv()


def extract() -> dict:
    """Extracts data from OpenAQ API for France (ID: 22).

    Measurements can only be extracted once locations data is transformed.
    This is because sensors IDs, stored within locations data, are needed to
    fetch measurement data.

    Returns:
        dict: Extracted JSON data for countries, pollutants, and locations.
    """
    api_key = os.getenv("OPENAQ_API_KEY")
    base_url = "https://api.openaq.org/v3/"
    headers = {"X-API-Key": api_key}

    with httpx.Client(base_url=base_url, headers=headers) as client:
        countries_json = [{"id": 22, "code": "FR", "name": "France"}]
        pollutants_json = client.get("countries/22").json()
        locations_json = client.get(
            "locations", params={"countries_id": 22, "limit": 1000}
        ).json()

    return {
        "countries": countries_json,
        "pollutants": pollutants_json,
        "locations": locations_json,
    }
