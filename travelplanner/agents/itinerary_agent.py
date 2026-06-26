import logging
import os
import re

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

from agents.utils import strip_thinking
from config import OLLAMA_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


class ItineraryAgent:

    def __init__(self):
        self._llm = None

    def _get_llm(self, days: int):
        if self._llm is None:
            self._llm = ChatOllama(
                model=OLLAMA_MODEL,
                temperature=0.7,
                num_predict=max(2048, days * 400),
                base_url=OLLAMA_URL,
                client_kwargs={"timeout": 300},
            )
        return self._llm

    def build_itinerary(
        self,
        destination: str,
        days: int,
        planner_summary: str = "",
        attractions: list | None = None,
        rag_data: dict | None = None,
    ) -> dict:
        logger.info("Generando itinerario de %d días para '%s'", days, destination)

        attractions_text = "\n".join(
            f"- {a.get('name', a.get('nombre', str(a)))}"
            for a in (attractions or [])
        ) or "Sin atracciones específicas — usa tu conocimiento del destino."

        rag = rag_data or {}
        rag_parts = []
        if rag.get("weather"):
            rag_parts.append(f"Clima: {rag['weather'][:200]}")
        if rag.get("transport"):
            rag_parts.append(f"Transporte: {rag['transport'][:200]}")
        if rag.get("tips"):
            rag_parts.append(f"Consejos locales: {'; '.join(rag['tips'][:3])}")
        if rag.get("events"):
            rag_parts.append(f"Eventos: {'; '.join(rag['events'][:2])}")
        if rag.get("neighborhoods"):
            rag_parts.append(f"Barrios recomendados: {'; '.join(rag['neighborhoods'][:3])}")
        rag_context = "\n".join(rag_parts) if rag_parts else "Usa tu conocimiento general del destino."

        with open("prompts/itinerary.txt", "r", encoding="utf-8") as f:
            prompt_text = f.read()

        prompt_template = ChatPromptTemplate.from_template(prompt_text)
        chain = prompt_template | self._get_llm(days)

        response = chain.invoke({
            "destination": destination,
            "days": days,
            "planner_summary": planner_summary or f"Destino: {destination}, {days} días.",
            "attractions_text": attractions_text,
            "rag_context": rag_context,
        })

        raw = strip_thinking(response.content)
        logger.debug("Itinerario raw (primeros 500 chars): %s", raw[:500])

        parsed_days = self._parse_days(raw, destination, days, attractions or [])

        return {
            "destination": destination,
            "days": days,
            "itinerary": parsed_days,
        }

    def _parse_days(self, raw: str, destination: str, days: int, attractions: list) -> list:
        sections = re.split(r'(?:^|\n)DÍA\s*(\d+)\s*:', raw, flags=re.IGNORECASE | re.MULTILINE)
        result = []

        if len(sections) > 1:
            blocks = []
            current = None
            for part in sections[1:]:
                part = part.strip()
                if part.isdigit():
                    if current:
                        blocks.append(current)
                    current = {"num": int(part), "text": ""}
                elif current is not None:
                    current["text"] = part
            if current:
                blocks.append(current)

            for b in blocks:
                lines = b["text"].split("\n")
                title = ""
                description_lines = []
                activities = []

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    lower = line.lower()
                    if lower.startswith("actividades:"):
                        raw_acts = line[len("actividades:"):].strip()
                        raw_acts = raw_acts.replace("[", "").replace("]", "")
                        activities = [a.strip().strip("-").strip() for a in raw_acts.split("|") if a.strip()]
                        if not activities:
                            activities = [a.strip() for a in raw_acts.split(",") if a.strip()]
                    elif not title:
                        title = line.replace("**", "").replace("*", "").strip()
                    else:
                        description_lines.append(line)

                description = " ".join(description_lines) if description_lines else ""
                cleaned_activities = [
                    a.replace("**", "").replace("*", "").strip()
                    for a in activities if a
                ]

                if not cleaned_activities and attractions:
                    start = (b["num"] - 1) * 3
                    cleaned_activities = [
                        a.get("name", a.get("nombre", str(a)))
                        for a in attractions[start:start + 3]
                    ]

                result.append({
                    "title": title or f"Día {b['num']} en {destination}",
                    "description": description or f"Exploración del día {b['num']} en {destination}.",
                    "suggested_activities": cleaned_activities,
                })
        else:
            for i in range(days):
                acts = [
                    a.get("name", a.get("nombre", str(a)))
                    for a in attractions[i * 3:(i + 1) * 3]
                ] if attractions else []
                result.append({
                    "title": f"Día {i + 1} en {destination}",
                    "description": f"Exploración del día {i + 1} en {destination}.",
                    "suggested_activities": acts,
                })

        while len(result) < days:
            result.append({
                "title": f"Día {len(result) + 1} en {destination}",
                "description": f"Continúa explorando {destination}.",
                "suggested_activities": [],
            })

        return result[:days]
