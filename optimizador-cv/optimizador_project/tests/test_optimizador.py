"""
Tests para el Optimizador de Currículums (arquitectura CV Matcher).
"""

import pytest
from pathlib import Path

from optimizador.models.schemas import (
    JobAnalysis,
    CVAnalysis,
    ATSScore,
    WorkflowState,
)
from optimizador.utils.pdf_loader import load_document
from optimizador.config import OFERTAS_DIR, DOCS_DIR


# ==================== FIXTURES ====================

@pytest.fixture
def sample_cv_path():
    """Ruta al CV de ejemplo."""
    return Path(__file__).parent.parent / "data" / "sample_cv.txt"


@pytest.fixture
def sample_job_posting_path():
    """Ruta a la oferta de ejemplo."""
    return Path(__file__).parent.parent / "data" / "sample_job_posting.txt"


@pytest.fixture
def sample_cv_text(sample_cv_path):
    """Carga el texto del CV de ejemplo."""
    if sample_cv_path.exists():
        return load_document(str(sample_cv_path))
    return "Nombre: Juan Pérez\nExperiencia: 5 años en Python, SQL, Docker"


@pytest.fixture
def sample_job_text(sample_job_posting_path):
    """Carga el texto de la oferta de ejemplo."""
    if sample_job_posting_path.exists():
        return load_document(str(sample_job_posting_path))
    return "Buscamos desarrollador Python con 3+ años de experiencia"


# ==================== TESTS DE MODELOS ====================

class TestModels:
    """Tests para los modelos Pydantic."""

    def test_job_analysis_creation(self):
        """Verifica que JobAnalysis se crea correctamente."""
        job = JobAnalysis(
            job_title="Desarrollador Python",
            required_skills=["Python", "Django", "SQL"],
            soft_skills=["Trabajo en equipo"],
            years_experience=3,
            seniority_level="Mid",
            keywords_ats=["python", "django", "sql"],
            responsibilities=["Desarrollar APIs"],
            technologies=["Python", "PostgreSQL"],
            salary_range="40k-50k",
        )
        assert job.job_title == "Desarrollador Python"
        assert len(job.required_skills) == 3
        assert job.years_experience == 3

    def test_cv_analysis_creation(self):
        """Verifica que CVAnalysis se crea correctamente."""
        cv = CVAnalysis(
            candidate_name="Juan Pérez",
            current_skills=["Python", "SQL"],
            experience_years=5,
            education=["Ingeniería Informática"],
            certifications=["AWS Certified"],
            strengths=["Experiencia en Python"],
            gaps=["Falta Django"],
        )
        assert cv.candidate_name == "Juan Pérez"
        assert cv.experience_years == 5

    def test_ats_score_creation(self):
        """Verifica que ATSScore se crea correctamente."""
        score = ATSScore(
            keyword_match=85.0,
            format_score=90.0,
            completeness=80.0,
            overall_score=85.0,
        )
        assert score.overall_score == 85.0
        assert score.keyword_match >= 0

    def test_workflow_state_defaults(self):
        """Verifica valores por defecto de WorkflowState."""
        state = WorkflowState(cv_text="Mi CV aquí")
        assert state.cv_text == "Mi CV aquí"
        assert state.job_posting_text is None
        assert state.current_step == "start"
        assert state.errors == []
        assert state.found_keywords == []

    def test_workflow_state_with_matched_offer(self):
        """Verifica WorkflowState con offer matcheada."""
        state = WorkflowState(
            cv_text="Mi CV",
            job_posting_text="Oferta matcheada",
            matched_offer_filename="01_python_senior",
            offer_match_score=0.75,
        )
        assert state.matched_offer_filename == "01_python_senior"
        assert state.offer_match_score == 0.75


# ==================== TESTS DE CONFIG ====================

class TestConfig:
    """Tests para la configuración."""

    def test_ofertas_dir_exists(self):
        """Verifica que la carpeta de ofertas existe."""
        assert OFERTAS_DIR.exists()

    def test_docs_dir_exists(self):
        """Verifica que la carpeta de docs existe."""
        assert DOCS_DIR.exists()

    def test_ofertas_has_files(self):
        """Verifica que hay ofertas en la carpeta."""
        offer_files = list(OFERTAS_DIR.glob("*.txt")) + list(OFERTAS_DIR.glob("*.pdf"))
        assert len(offer_files) > 0, "Debe haber al menos una oferta en ofertas/"

    def test_docs_has_files(self):
        """Verifica que hay docs en la carpeta."""
        doc_files = list(DOCS_DIR.glob("*.txt")) + list(DOCS_DIR.glob("*.md"))
        assert len(doc_files) > 0, "Debe haber al menos un documento en docs/"


# ==================== TESTS DE UTILIDADES ====================

class TestUtils:
    """Tests para utilidades."""

    def test_load_txt_document(self, sample_cv_path):
        """Verifica carga de documentos TXT."""
        if sample_cv_path.exists():
            text = load_document(str(sample_cv_path))
            assert len(text) > 0
            assert isinstance(text, str)


# ==================== TESTS DE AGENTE (requiere Ollama) ====================

@pytest.mark.integration
class TestCVReviewerAgent:
    """Tests para el agente CV Reviewer (requiere Ollama corriendo)."""

    @pytest.fixture
    def cv_reviewer(self):
        """Crea instancia del agente (skip si Ollama no está disponible)."""
        try:
            from optimizador.agents.cv_reviewer import CVReviewerAgent
            return CVReviewerAgent()
        except Exception:
            pytest.skip("Ollama no disponible")

    def test_extract_json(self, cv_reviewer):
        """Verifica extracción de JSON de texto."""
        text = 'Aquí está el resultado: {"key": "value"} y más texto.'
        result = cv_reviewer._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_no_json(self, cv_reviewer):
        """Verifica error cuando no hay JSON."""
        with pytest.raises(ValueError):
            cv_reviewer._extract_json("No hay JSON aquí")

    def test_repair_json_trailing_comma(self, cv_reviewer):
        """Verifica reparación de comas colgantes."""
        bad_json = '{"a": 1, "b": 2,}'
        repaired = cv_reviewer._repair_json(bad_json)
        assert repaired == '{"a": 1, "b": 2}'

    def test_repair_json_missing_comma(self, cv_reviewer):
        """Verifica reparación de comas faltantes."""
        bad_json = '{"a": 1 "b": 2}'
        repaired = cv_reviewer._repair_json(bad_json)
        assert '"a": 1, "b"' in repaired or '"a": 1,' in repaired


# ==================== TESTS DE OFERTA STORE (requiere Ollama) ====================

@pytest.mark.integration
class TestOfferStore:
    """Tests para el store de ofertas (requiere Ollama corriendo)."""

    @pytest.fixture
    def offer_store(self):
        """Crea instancia del store (skip si Ollama no está disponible)."""
        try:
            from optimizador.rag.offer_store import JobOfferStore
            return JobOfferStore()
        except Exception:
            pytest.skip("Ollama no disponible para embeddings")

    def test_offer_store_has_offers(self, offer_store):
        """Verifica que el store tiene ofertas cargadas."""
        offers = offer_store.list_offers()
        assert len(offers) > 0

    def test_match_best_offer_returns_result(self, offer_store):
        """Verifica que match_best_offer devuelve resultado válido."""
        cv_text = "Desarrollador Python con experiencia en Django, PostgreSQL y Docker"
        result = offer_store.match_best_offer(cv_text)
        assert result is not None
        assert "offer_text" in result
        assert "offer_filename" in result
        assert "similarity_score" in result
        assert result["similarity_score"] >= 0
