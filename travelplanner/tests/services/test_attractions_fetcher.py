from dotenv import load_dotenv
load_dotenv()

from services.attractions.attractions_fetcher import AttractionsFetcher


def test_attractions_fetcher():

    results = AttractionsFetcher.get_attractions_for_city("malaga", limit=3, currency="EUR")

    print("Atracciones:", results)

    assert isinstance(results, list)
    assert len(results) > 0
    assert "name" in results[0]


if __name__ == "__main__":
    test_attractions_fetcher()
