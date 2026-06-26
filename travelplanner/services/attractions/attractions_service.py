import requests

from services.config import RAPIDAPI_HOST, RAPIDAPI_KEY


class AttractionsService:

    BASE_URL = "https://booking-com15.p.rapidapi.com/api/v1/attraction/searchAttractions"

    @staticmethod
    def safe_get(obj, *keys):
        """
        Permite acceder a claves anidadas sin romper si algo es None.
        Ejemplo:
        safe_get(p, "reviewsStats", "combinedNumericStats", "average")
        """
        for key in keys:
            if not isinstance(obj, dict):
                return None
            obj = obj.get(key)
        return obj

    @staticmethod
    def search_attractions(encoded_id: str, page: int = 1, sort_by: str = "trending",
                           currency: str = "EUR", language: str = "en-us"):

        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": RAPIDAPI_HOST,
            "x-rapidapi-key": RAPIDAPI_KEY
        }

        params = {
            "id": encoded_id,
            "sortBy": sort_by,
            "page": page,
            "currency_code": currency,
            "languagecode": language
        }

        response = requests.get(AttractionsService.BASE_URL, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Error en API: {response.status_code} - {response.text}")

        products = response.json().get("data", {}).get("products", [])

        normalized = []

        for p in products:
            normalized.append({
                "id": p.get("id"),
                "name": p.get("name"),
                "description": p.get("shortDescription"),
                "price": AttractionsService.safe_get(p, "representativePrice", "chargeAmount"),
                "currency": AttractionsService.safe_get(p, "representativePrice", "currency"),
                "rating": AttractionsService.safe_get(p, "reviewsStats", "combinedNumericStats", "average"),
                "reviews": AttractionsService.safe_get(p, "reviewsStats", "allReviewsCount"),
                "photo": AttractionsService.safe_get(p, "primaryPhoto", "small"),
                "city": AttractionsService.safe_get(p, "ufiDetails", "bCityName"),
                "country": AttractionsService.safe_get(p, "ufiDetails", "url", "country")
            })

        return normalized
