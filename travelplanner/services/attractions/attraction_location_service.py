import requests

from services.config import RAPIDAPI_HOST, RAPIDAPI_KEY


class AttractionLocationService:

    BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1/attraction/searchLocation"

    @staticmethod
    def search_location(query: str, language: str = "en-us"):
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY
        }

        params = {
            "query": query,
            "languagecode": language
        }

        response = requests.get(AttractionLocationService.BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error en API: {response.status_code} - {response.text}")

        data = response.json().get("data", {})

        destinations = data.get("destinations", [])

        if not destinations:
            return None

        # Tomamos el primer destino (el más relevante)
        return destinations[0]
