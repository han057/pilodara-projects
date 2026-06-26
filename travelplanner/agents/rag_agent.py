import logging

logger = logging.getLogger(__name__)


class RAGAgent:

    def run(self, state):
        query = state.get("user_query") or state.get("destination_city")
        if not query:
            logger.warning("RAGAgent: no query provided")
            return {**state, "rag_data": {}}

        logger.info("RAGAgent: consultando Chroma para '%s'", query)

        try:
            from rag.rag_query import RAGQuery

            chunks = RAGQuery().search(query)
            logger.info("RAGAgent: %d chunks recuperados", len(chunks))

            rag_data = {
                "weather": None,
                "transport": None,
                "events": [],
                "neighborhoods": [],
                "tips": [],
            }

            for c in chunks:
                text = c.get("content", "").lower()
                cat = (c.get("metadata") or {}).get("categoria", "")

                if cat == "clima" or "clima" in text or "temperatura" in text:
                    rag_data["weather"] = c["content"]
                if cat == "transporte" or "transporte" in text or "metro" in text or "bus" in text:
                    rag_data["transport"] = c["content"]
                if cat == "eventos" or "evento" in text or "festival" in text:
                    rag_data["events"].append(c["content"])
                if cat == "barrios" or "barrio" in text or "zona" in text:
                    rag_data["neighborhoods"].append(c["content"])
                if cat == "tips" or "tip" in text or "consejo" in text:
                    rag_data["tips"].append(c["content"])

            logger.info(
                "RAGAgent: weather=%s transport=%s events=%d neighborhoods=%d tips=%d",
                bool(rag_data["weather"]),
                bool(rag_data["transport"]),
                len(rag_data["events"]),
                len(rag_data["neighborhoods"]),
                len(rag_data["tips"]),
            )

            return {**state, "rag_data": rag_data}
        except Exception:
            logger.exception("RAGAgent: error consultando Chroma")
            return {**state, "rag_data": {}}


rag_agent = RAGAgent().run
