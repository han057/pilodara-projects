from dotenv import load_dotenv
load_dotenv()

from agents.rag_agent import rag_agent


def test_rag_agent():

    # Estado simulado que llega desde classifier_agent
    state = {
        "destination_city": "sevilla",
        "user_query": "qué clima hay en sevilla en julio?"
    }

    result = rag_agent(state)

    assert "rag_data" in result
    rag = result["rag_data"]

    # Validar estructura mínima
    assert isinstance(rag, dict)

    # Las claves pueden variar según tus PDFs, pero estas son estándar
    expected_keys = ["weather", "transport", "events", "neighborhoods", "tips"]

    for key in expected_keys:
        assert key in rag, f"Falta clave en RAG: {key}"

    # Validar que al menos uno tenga contenido
    assert any(rag[k] for k in expected_keys), "RAG devolvió todo vacío"

    print("RAG OK:", rag)
