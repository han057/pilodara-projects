from services.attractions.attraction_location_service import AttractionLocationService
from services.attractions.attractions_service import AttractionsService


class AttractionsFetcher:

    @staticmethod
    def get_attractions_for_city(city: str, limit: int = 5, currency: str = "EUR", language: str = "en-us"):
        """
        Servicio combinado:
        1. Busca el ID codificado de la ciudad
        2. Busca las atracciones reales
        3. Devuelve una lista normalizada (top N)
        """

        # 1. Obtener ID codificado desde SearchLocation
        location = AttractionLocationService.search_location(city, language)

        if not location or "id" not in location:
            return []

        encoded_id = location["id"]

        # 2. Buscar atracciones reales
        attractions = AttractionsService.search_attractions(
            encoded_id=encoded_id,
            page=1,
            sort_by="trending",
            currency=currency,
            language=language
        )

        # 3. Limitar resultados
        return attractions[:limit]
