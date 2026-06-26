def fetch_attractions_node(state):
    city = state.get("destination_city")
    limit = state.get("attractions_limit", 5)
    currency = state.get("currency", "EUR")
    language = state.get("language", "en-us")

    try:
        from services.attractions.attractions_fetcher import AttractionsFetcher

        attractions = AttractionsFetcher.get_attractions_for_city(
            city=city,
            limit=limit,
            currency=currency,
            language=language
        )
        if not isinstance(attractions, list):
            attractions = []
    except Exception:
        attractions = []

    return {
        **state,
        "attractions": attractions
    }
