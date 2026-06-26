"""
CV Reviewer Agent: Agente unificado que realiza TODO en una sola llamada al LLM.
1. Analiza la oferta de empleo
2. Analiza el CV del candidato
3. Optimiza el CV para la oferta
4. Evalúa compatibilidad ATS
5. Realiza revisión final
"""

import json
import re
import logging

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

from optimizador.models.schemas import (
    JobAnalysis, CVAnalysis, CVOptimizationResult,
    ATSScore, ATSReviewResult,
)
from optimizador.config import LLM_CONFIG, PROMPTS, AGENTS_CONFIG
from optimizador.rag.vector_store import get_knowledge_base

logger = logging.getLogger(__name__)


class CVReviewerAgent:
    """Agente unificado: analiza oferta + CV, optimiza, evalúa ATS y revisa."""

    def __init__(self):
        self.config = AGENTS_CONFIG["cv_reviewer"]
        self.llm = ChatOllama(
            model=self.config["model"],
            temperature=self.config["temperature"],
            base_url=LLM_CONFIG["base_url"],
            request_timeout=LLM_CONFIG["request_timeout"],
        )
        self.prompt_template = PROMPTS["cv_reviewer"]

        try:
            self.knowledge_base = get_knowledge_base()
        except Exception as e:
            logger.warning(f"No se pudo inicializar RAG: {e}. Continuando sin RAG.")
            self.knowledge_base = None

    def review(self, job_posting_text: str, cv_text: str, max_retries: int = 2) -> dict:
        """
        Ejecuta el análisis completo en una sola llamada.
        Reintenta hasta max_retries veces si el JSON no es válido.

        Returns:
            dict con todas las claves del resultado
        """
        logger.info("Iniciando análisis completo (CV Reviewer)...")

        rag_context = self._get_rag_context()
        prompt = self.prompt_template.format(
            job_posting_text=job_posting_text,
            cv_text=cv_text,
            rag_context=rag_context,
        )

        last_error = None
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Intento {attempt}/{max_retries}...")
                message = HumanMessage(content=prompt)
                response = self.llm.invoke([message])
                response_text = response.content
                logger.debug(f"Respuesta LLM recibida ({len(response_text)} chars)")

                result = self._parse_response(response_text, cv_text)

                logger.info(
                    f"Análisis completado: ATS {result['ats_score'].overall_score:.0f}%, "
                    f"{len(result['found_keywords'])} keywords encontradas"
                )
                return result

            except (json.JSONDecodeError, ValueError) as e:
                last_error = e
                logger.warning(f"Intento {attempt} falló: {e}")
                if attempt < max_retries:
                    # Reforzar prompt para el reintento
                    prompt = prompt + (
                        "\n\nIMPORTANTE: Tu respuesta anterior tenía un error de formato JSON. "
                        "Asegúrate de que el JSON sea válido: usa comas entre campos, "
                        "no dejes comas colgantes, y cierra todas las llaves correctamente."
                    )
                continue
            except Exception as e:
                logger.error(f"Error inesperado en CV Reviewer: {e}")
                raise

        raise ValueError(
            f"No se pudo obtener una respuesta válida tras {max_retries} intentos. "
            f"Último error: {last_error}"
        )

    def _get_rag_context(self) -> str:
        if self.knowledge_base is None:
            return "No hay contexto disponible de la base de conocimiento."
        try:
            query = "mejores prácticas para currículum profesional optimizado para ATS"
            return self.knowledge_base.get_context_for_query(query, k=3)
        except Exception as e:
            logger.warning(f"Error RAG: {e}")
            return "No se pudo obtener contexto de la base de conocimiento."

    def _parse_response(self, response_text: str, original_cv: str) -> dict:
        try:
            json_str = self._extract_json(response_text)
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON inválido, intentando reparar: {e}")
            try:
                json_str = self._repair_json(json_str)
                data = json.loads(json_str)
            except (json.JSONDecodeError, ValueError) as e2:
                logger.error(f"JSON no se pudo reparar: {e2}")
                raise ValueError(f"No se pudo parsear la respuesta del LLM: {e2}")
        except ValueError as e:
            logger.error(f"Error extrayendo JSON: {e}")
            raise ValueError(f"No se pudo parsear la respuesta del LLM: {e}")

        # --- Job Analysis ---
        ja = data.get("job_analysis", {})
        job_analysis = JobAnalysis(
            job_title=ja.get("job_title", "Unknown"),
            required_skills=ja.get("required_skills", []),
            soft_skills=ja.get("soft_skills", []),
            years_experience=int(ja.get("years_experience", 0)),
            seniority_level=ja.get("seniority_level", "Mid"),
            keywords_ats=ja.get("keywords_ats", []),
            responsibilities=ja.get("responsibilities", []),
            technologies=ja.get("technologies", []),
            salary_range=ja.get("salary_range"),
        )

        # --- CV Analysis ---
        ca = data.get("cv_analysis", {})
        cv_analysis = CVAnalysis(
            candidate_name=ca.get("candidate_name", "Unknown"),
            current_skills=ca.get("current_skills", []),
            experience_years=int(ca.get("experience_years", 0)),
            education=ca.get("education", []),
            certifications=ca.get("certifications", []),
            strengths=ca.get("strengths", []),
            gaps=ca.get("gaps", []),
        )

        # --- ATS Score ---
        ats_data = data.get("ats_score", {})
        ats_score = ATSScore(
            keyword_match=float(ats_data.get("keyword_match", 0.0)),
            format_score=float(ats_data.get("format_score", 0.0)),
            completeness=float(ats_data.get("completeness", 0.0)),
            overall_score=float(ats_data.get("overall_score", 0.0)),
        )

        # --- Keywords con validación contra CV real ---
        final_cv = data.get("final_cv", "") or data.get("optimized_cv", "")
        found_keywords = data.get("found_keywords", [])
        missing_keywords = data.get("missing_keywords", [])

        # Validar: solo marcar como "found" lo que realmente está en el CV
        cv_lower = final_cv.lower()
        verified_found = []
        moved_to_missing = []
        for kw in found_keywords:
            if kw.lower().strip() in cv_lower:
                verified_found.append(kw)
            else:
                moved_to_missing.append(kw)
        # Deduplicar missing
        all_missing = missing_keywords + moved_to_missing
        seen = set()
        unique_missing = []
        for kw in all_missing:
            kw_lower = kw.lower().strip()
            if kw_lower not in seen:
                seen.add(kw_lower)
                unique_missing.append(kw)

        return {
            "job_analysis": job_analysis,
            "cv_analysis": cv_analysis,
            "optimized_cv": data.get("optimized_cv", ""),
            "changes_made": data.get("changes_made", []),
            "keywords_added": data.get("keywords_added", []),
            "match_score": float(data.get("match_score", 0.0)),
            "ats_score": ats_score,
            "found_keywords": verified_found,
            "missing_keywords": unique_missing,
            "final_cv": final_cv,
            "recommendations": data.get("recommendations", []),
            "improvements_applied": data.get("improvements_applied", []),
        }

    def _extract_json(self, text: str) -> str:
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No se encontró JSON en la respuesta")
        return text[start_idx:end_idx]

    def _repair_json(self, json_str: str) -> str:
        """
        Intenta reparar errores comunes de JSON generados por modelos pequeños:
        - Comas colgantes antes de } o ]
        - Falta de comas entre campos
        - Strings sin cerrar
        """
        repaired = json_str

        # Eliminar comas colgantes antes de } o ]
        repaired = re.sub(r',\s*}', '}', repaired)
        repaired = re.sub(r',\s*]', ']', repaired)

        # Añadir coma faltante entre valor y siguiente clave
        # Pattern: "value" "key" → "value", "key"
        repaired = re.sub(r'"\s+"', '", "', repaired)
        # Pattern: } "key" → }, "key"
        repaired = re.sub(r'}\s+"', '}, "', repaired)
        # Pattern: ] "key" → ], "key"
        repaired = re.sub(r']\s+"', '], "', repaired)
        # Pattern: number "key" → number, "key"
        repaired = re.sub(r'(\d)\s+"', r'\1, "', repaired)

        # Cerrar strings sin cerrar (líneas con " abierto)
        lines = repaired.split('\n')
        fixed_lines = []
        for line in lines:
            stripped = line.rstrip()
            # Si la línea tiene un número impar de comillas, probablemente falta una
            quote_count = stripped.count('"') - stripped.count('\\"')
            if quote_count % 2 != 0 and not stripped.endswith(','):
                stripped = stripped + '"'
            fixed_lines.append(stripped)
        repaired = '\n'.join(fixed_lines)

        logger.debug("JSON reparado, intentando parsear...")
        return repaired


def create_cv_reviewer() -> CVReviewerAgent:
    """Factory para crear instancia del agente."""
    return CVReviewerAgent()
