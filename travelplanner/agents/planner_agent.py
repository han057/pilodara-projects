import logging
import os

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from agents.utils import strip_thinking, format_history
from config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class PlannerAgent:

    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            self._llm = ChatOllama(
                model=OLLAMA_MODEL,
                temperature=0.7,
                num_predict=2048,
                base_url=OLLAMA_URL,
                client_kwargs={"timeout": 300},
            )
        return self._llm

    def plan_trip(
        self,
        destination: str,
        days: int,
        context: str = "",
        conversation_history: list | None = None,
    ) -> dict:
        logger.info("Planificando viaje a '%s' (%d días)", destination, days)

        history_text = format_history(conversation_history or [])

        context_parts = []
        if history_text:
            context_parts.append(history_text)
        if context:
            context_parts.append(f"Información sobre el destino:\n{context}")

        full_context = "\n\n".join(context_parts) if context_parts else "Sin información adicional disponible."

        with open("prompts/planner.txt", "r", encoding="utf-8") as f:
            prompt_text = f.read()

        prompt_template = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt_template | self.llm

        response = chain.invoke({
            "destination": destination,
            "duration_days": days,
            "context": full_context,
        })

        summary = strip_thinking(response.content)

        return {
            "destination": destination,
            "duration_days": days,
            "summary": summary,
            "status": "success",
            "mock": False,
        }
