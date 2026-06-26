from dotenv import load_dotenv
load_dotenv()

from graph.nodes import fetch_attractions_node


def test_fetch_attractions_node():

    state = {
        "destination_city": "málaga",
        "attractions_limit": 3,
        "currency": "EUR",
        "language": "en-us"
    }

    result = fetch_attractions_node(state)

    assert "attractions" in result
    assert isinstance(result["attractions"], list)
    assert len(result["attractions"]) > 0

    attraction = result["attractions"][0]
    assert "name" in attraction
    assert "photo" in attraction
    assert "rating" in attraction or attraction["rating"] is None

    print("Atracciones OK:", result["attractions"][:2])
