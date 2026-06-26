"""
LangGraph Workflow: Orquestador con matching de ofertas automático.
Flujo: START → match_offer → review_cv → END
"""

import logging

from langgraph.graph import StateGraph, START, END

from optimizador.models.schemas import WorkflowState
from optimizador.agents.cv_reviewer import create_cv_reviewer
from optimizador.rag.offer_store import get_offer_store

logger = logging.getLogger(__name__)


class CVOptimizationWorkflow:
    """Orquestador de workflow usando LangGraph StateGraph."""

    def __init__(self):
        self.cv_reviewer = create_cv_reviewer()
        self.offer_store = get_offer_store()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """
        Construye el StateGraph del workflow.
        Flujo: START → match_offer → review_cv → END
        """
        graph_builder = StateGraph(WorkflowState)

        graph_builder.add_node("match_offer", self._match_offer_node)
        graph_builder.add_node("review_cv", self._review_cv_node)

        graph_builder.add_edge(START, "match_offer")
        graph_builder.add_edge("match_offer", "review_cv")
        graph_builder.add_edge("review_cv", END)

        return graph_builder.compile()

    def _match_offer_node(self, state: WorkflowState) -> dict:
        """
        Nodo 1: Busca la oferta más compatible con el CV usando embeddings.
        """
        logger.info("[MATCH OFFER] Buscando oferta compatible con el CV...")

        try:
            result = self.offer_store.match_best_offer(state.cv_text)

            if result is None:
                return {
                    "current_step": "error",
                    "errors": ["No se encontró ninguna oferta compatible. "
                               "Verifica que hay ofertas en la carpeta ofertas/"],
                }

            logger.info(
                f"Oferta matcheada: {result['offer_filename']} "
                f"(similitud: {result['similarity_score']:.3f})"
            )

            return {
                "job_posting_text": result["offer_text"],
                "matched_offer_filename": result["offer_filename"],
                "offer_match_score": result["similarity_score"],
                "current_step": "offer_matched",
            }

        except Exception as e:
            logger.error(f"Error en matching de ofertas: {e}")
            return {
                "current_step": "error",
                "errors": [f"Error buscando oferta compatible: {e}"],
            }

    def _review_cv_node(self, state: WorkflowState) -> dict:
        """
        Nodo 2: El CV Reviewer optimiza el CV para la oferta matcheada.
        """
        logger.info("[CV REVIEWER] Ejecutando análisis completo...")

        if not state.job_posting_text:
            return {
                "current_step": "error",
                "errors": ["No hay oferta de empleo para analizar (match falló)"],
            }

        try:
            result = self.cv_reviewer.review(
                job_posting_text=state.job_posting_text,
                cv_text=state.cv_text,
            )

            return {
                "job_analysis": result["job_analysis"],
                "cv_analysis": result["cv_analysis"],
                "optimized_cv": result["optimized_cv"],
                "changes_made": result["changes_made"],
                "keywords_added": result["keywords_added"],
                "match_score": result["match_score"],
                "ats_score": result["ats_score"],
                "final_cv": result["final_cv"],
                "missing_keywords": result["missing_keywords"],
                "found_keywords": result["found_keywords"],
                "ats_recommendations": result["recommendations"],
                "improvements_applied": result["improvements_applied"],
                "current_step": "complete",
            }

        except Exception as e:
            logger.error(f"Error en CV Reviewer: {e}")
            return {
                "current_step": "error",
                "errors": [f"Error en análisis: {e}"],
            }

    def invoke(self, cv_text: str) -> WorkflowState:
        """Ejecuta el workflow completo (solo necesita el CV)."""
        logger.info("=" * 60)
        logger.info("INICIANDO WORKFLOW DE OPTIMIZACIÓN DE CV")
        logger.info("=" * 60)

        initial_state = {
            "cv_text": cv_text,
            "current_step": "start",
        }

        try:
            result_dict = self.graph.invoke(initial_state)
            final_state = WorkflowState(**result_dict)
            logger.info("=" * 60)
            logger.info("WORKFLOW COMPLETADO EXITOSAMENTE")
            logger.info("=" * 60)
            return final_state

        except Exception as e:
            logger.error(f"Error ejecutando workflow: {e}")
            return WorkflowState(
                cv_text=cv_text,
                current_step="error",
                errors=[str(e)],
            )


def create_workflow() -> CVOptimizationWorkflow:
    """Factory para crear instancia del workflow."""
    return CVOptimizationWorkflow()
