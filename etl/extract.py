"""Handles data extraction from OpenAQ API and returns JSON responses."""

import os

from dotenv import load_dotenv
import httpx

load_dotenv()

API_KEY = os.getenv("OPENAQ_API_KEY")
BASE_URL = "https://api.openaq.org/v3/"
HEADERS = {"X-API-Key": API_KEY}


def api_call(endpoint: str, params: dict = None) -> dict:
    """Makes an API request to OpenAQ.

    Args:
        endpoint (str): The API endpoint to query.
        params (dict, optional): Query parameters for the API request.

    Returns:
        dict: The JSON response from the API.

    Raises:
        ValueError: If the request fails.
    """
    with httpx.Client(base_url=BASE_URL, headers=HEADERS) as client:
        response = client.get(endpoint, params=params)
        if response.status_code == 200:
            return response.json()
        raise ValueError(f"Request failed with status code: {response.status_code}")


def extract_data() -> dict:
    """Extracts data from OpenAQ API for France (ID: 22).

    Measurements can only be extracted once locations data is transformed.
    This is because sensors IDs, stored within locations data, are needed to
    fetch measurement data.

    Returns:
        dict: Extracted JSON data for countries, pollutants, and locations.
    """
    countries_json = [{"id": 22, "code": "FR", "name": "France"}]
    pollutants_json = api_call("countries/22")
    locations_json = api_call("locations", {"countries_id": 22, "limit": 1000})

    return {
        "countries": countries_json,
        "pollutants": pollutants_json,
        "locations": locations_json,
    }
