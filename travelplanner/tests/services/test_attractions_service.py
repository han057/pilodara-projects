from dotenv import load_dotenv
load_dotenv()

from services.attractions.attraction_location_service import AttractionLocationService
from services.attractions.attractions_service import AttractionsService


def test_search_attractions():

    # 1. Buscar ID codificado desde SearchLocation
    loc = AttractionLocationService.search_location("malaga")
    assert loc is not None
    assert "id" in loc

    encoded_id = loc["id"]
    print("ID codificado:", encoded_id)

    # 2. Buscar atracciones reales
    results = AttractionsService.search_attractions(
        encoded_id=encoded_id,
        page=1,
        sort_by="trending",
        currency="INR",
        language="en-us"
    )

    print("Primeras atracciones:", results[:3])

    assert isinstance(results, list)
    assert len(results) > 0
    assert "name" in results[0]


if __name__ == "__main__":
    test_search_attractions()
