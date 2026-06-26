"""
Modelos Pydantic para la estructura de datos del optimizador de CVs.
Define las estructuras de entrada y salida para todos los agentes.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ==================== JOB ANALYZER ====================

class JobAnalysis(BaseModel):
    """Resultado del análisis de la oferta de empleo"""
    job_title: str = Field(..., description="Título del puesto")
    required_skills: List[str] = Field(..., description="Habilidades técnicas requeridas")
    soft_skills: List[str] = Field(..., description="Habilidades blandas")
    years_experience: int = Field(..., description="Años de experiencia mínimos")
    seniority_level: str = Field(..., description="Junior / Mid / Senior")
    keywords_ats: List[str] = Field(..., description="Palabras clave para ATS")
    responsibilities: List[str] = Field(..., description="Responsabilidades del puesto")
    technologies: List[str] = Field(..., description="Tecnologías mencionadas")
    salary_range: Optional[str] = Field(None, description="Rango salarial (si aparece)")


# ==================== CV OPTIMIZER ====================

class CVAnalysis(BaseModel):
    """Análisis del CV original del candidato"""
    candidate_name: str = Field(..., description="Nombre del candidato")
    current_skills: List[str] = Field(..., description="Habilidades actuales")
    experience_years: int = Field(..., description="Años de experiencia total")
    education: List[str] = Field(..., description="Formación académica")
    certifications: List[str] = Field(..., description="Certificaciones profesionales")
    strengths: List[str] = Field(..., description="Puntos fuertes respecto a la oferta")
    gaps: List[str] = Field(..., description="Huecos/diferencias respecto a la oferta")


class CVOptimizationResult(BaseModel):
    """Resultado de la optimización del CV"""
    cv_analysis: CVAnalysis = Field(..., description="Análisis del CV original")
    optimized_cv: str = Field(..., description="CV optimizado completo")
    changes_made: List[str] = Field(..., description="Cambios realizados")
    keywords_added: List[str] = Field(..., description="Keywords añadidas al CV")
    match_score: float = Field(..., description="Score de compatibilidad (0-100)")


# ==================== ATS REVIEWER ====================

class ATSScore(BaseModel):
    """Puntuación ATS detallada"""
    keyword_match: float = Field(..., description="Coincidencia de keywords (0-100)")
    format_score: float = Field(..., description="Calidad del formato (0-100)")
    completeness: float = Field(..., description="Cobertura de requisitos (0-100)")
    overall_score: float = Field(..., description="Puntuación global (0-100)")


class ATSReviewResult(BaseModel):
    """Resultado de la revisión ATS y final"""
    ats_score: ATSScore = Field(..., description="Puntuaciones ATS detalladas")
    final_cv: str = Field(..., description="CV final después de correcciones")
    missing_keywords: List[str] = Field(..., description="Keywords que faltan")
    found_keywords: List[str] = Field(..., description="Keywords encontradas")
    recommendations: List[str] = Field(..., description="Recomendaciones finales")
    improvements_applied: List[str] = Field(..., description="Mejoras aplicadas en revisión final")


# ==================== WORKFLOW STATE ====================

class WorkflowState(BaseModel):
    """Estado global del workflow LangGraph"""
    # Inputs
    cv_text: str = Field(..., description="Texto del CV extraído del PDF")
    job_posting_text: Optional[str] = Field(None, description="Texto de la oferta (auto-matcheado)")
    
    # Offer matching
    matched_offer_filename: Optional[str] = Field(None, description="Archivo de oferta matcheada")
    offer_match_score: Optional[float] = Field(None, description="Similitud de la oferta matcheada")
    
    # Agent output
    job_analysis: Optional[JobAnalysis] = Field(None, description="Resultado del análisis de oferta")
    cv_analysis: Optional[CVAnalysis] = Field(None, description="Análisis del CV")
    optimized_cv: Optional[str] = Field(None, description="CV optimizado")
    changes_made: List[str] = Field(default_factory=list, description="Cambios realizados")
    keywords_added: List[str] = Field(default_factory=list, description="Keywords añadidas")
    match_score: Optional[float] = Field(None, description="Score de compatibilidad")
    
    # ATS output
    ats_score: Optional[ATSScore] = Field(None, description="Puntuación ATS")
    final_cv: Optional[str] = Field(None, description="CV final pulido")
    missing_keywords: List[str] = Field(default_factory=list, description="Keywords faltantes")
    found_keywords: List[str] = Field(default_factory=list, description="Keywords encontradas")
    ats_recommendations: List[str] = Field(default_factory=list, description="Recomendaciones ATS")
    improvements_applied: List[str] = Field(default_factory=list, description="Mejoras aplicadas")
    
    # Control
    current_step: str = Field(default="start", description="Paso actual del workflow")
    errors: List[str] = Field(default_factory=list, description="Errores encontrados")
