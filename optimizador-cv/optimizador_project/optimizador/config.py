"""
Configuración global del optimizador de CVs.
Define modelos, parámetros de RAG, y configuración del LLM.
"""

import os
from pathlib import Path

# ==================== RUTAS ====================

PROJECT_ROOT = Path(__file__).parent.parent
DOCS_DIR = PROJECT_ROOT / "docs"
OFERTAS_DIR = PROJECT_ROOT / "ofertas"
CHROMA_DB_DIR = PROJECT_ROOT.parent / "chroma_db"
DATA_DIR = PROJECT_ROOT / "data"

# Crear directorios si no existen
CHROMA_DB_DIR.mkdir(exist_ok=True)
DOCS_DIR.mkdir(exist_ok=True)
OFERTAS_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)


# ==================== LLM CONFIGURATION ====================

OLLAMA_API_BASE_URL = os.getenv(
    "OLLAMA_API_BASE_URL",
    os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
)

LLM_CONFIG = {
    "model": "gemma3:4b",
    "temperature_extraction": 0.1,      # Extracción precisa (Job Analyzer)
    "temperature_optimization": 0.4,    # Creatividad controlada (CV Optimizer)
    "temperature_review": 0.2,          # Revisión precisa (ATS Reviewer)
    "base_url": OLLAMA_API_BASE_URL,
    "request_timeout": 300,              # 5 minutos timeout
}


# ==================== RAG CONFIGURATION ====================

RAG_CONFIG = {
    "chunk_size": 500,
    "chunk_overlap": 50,
    "embedding_model": "nomic-embed-text",
    "base_url": OLLAMA_API_BASE_URL,
    "collection_name": "cv_knowledge_base",
    "persist_directory": str(CHROMA_DB_DIR),
    "top_k": 3,                         # Documentos a recuperar
}

OFERTAS_RAG_CONFIG = {
    "chunk_size": 1000,
    "chunk_overlap": 100,
    "embedding_model": "nomic-embed-text",
    "base_url": OLLAMA_API_BASE_URL,
    "collection_name": "job_offers",     # Colección independiente
    "persist_directory": str(CHROMA_DB_DIR),
    "top_k": 1,                         # Solo el mejor match
}


# ==================== PROMPT TEMPLATES ====================

PROMPTS = {
    "cv_reviewer": """Eres un experto en optimización de currículums y sistemas ATS (Applicant Tracking Systems).

## Oferta de empleo:
{job_posting_text}

## CV actual del candidato:
{cv_text}

## Mejores prácticas (de la base de conocimiento):
{rag_context}

## Tu tarea — realiza TODO en un solo análisis:

### Parte 1: Análisis de la oferta
Extrae de la oferta: título del puesto, habilidades técnicas requeridas, habilidades blandas, años de experiencia, nivel de seniority, palabras clave ATS, responsabilidades, tecnologías, rango salarial.

### Parte 2: Análisis del CV
Extrae del CV: nombre del candidato, habilidades actuales, años de experiencia, formación, certificaciones, puntos fuertes, huecos respecto a la oferta.

### Parte 3: Optimización del CV
Reescribe el CV completo optimizándolo para esta oferta específica:
- Añade palabras clave ATS de forma natural
- Destaca logros cuantificables
- Reordena secciones por relevancia
- NO inventes experiencia que el candidato no tenga
- NUNCA uses placeholders ni textos como "[insertar aquí]" o "[Placeholder for...]"
- El CV final debe estar completo y listo para enviar, sin corchetes ni marcadores
- IMPORTANTE: El CV solo debe contener información del CANDIDATO. NUNCA copies información de la oferta de empleo al CV (beneficios de la empresa, salario, ubicación, requisitos del puesto, etc.)

### Parte 4: Evaluación ATS
Evalúa el CV optimizado como si fueras un sistema ATS:
- ¿Qué keywords de la oferta están presentes en el CV optimizado?
- ¿Qué keywords faltan?
- Puntuaciones: keyword_match (0-100), format_score (0-100), completeness (0-100), overall_score (0-100)

### Parte 5: Revisión final
- Corrige errores gramaticales
- Elimina redundancias
- Mejora la redacción
- Uniformiza el formato

Devuelve un JSON válido con esta estructura EXACTA:
{{
    "job_analysis": {{
        "job_title": "...",
        "required_skills": [...],
        "soft_skills": [...],
        "years_experience": 0,
        "seniority_level": "...",
        "keywords_ats": [...],
        "responsibilities": [...],
        "technologies": [...],
        "salary_range": "..."
    }},
    "cv_analysis": {{
        "candidate_name": "...",
        "current_skills": [...],
        "experience_years": 0,
        "education": [...],
        "certifications": [...],
        "strengths": [...],
        "gaps": [...]
    }},
    "optimized_cv": "...",
    "changes_made": [...],
    "keywords_added": [...],
    "match_score": 0.0,
    "ats_score": {{
        "keyword_match": 0.0,
        "format_score": 0.0,
        "completeness": 0.0,
        "overall_score": 0.0
    }},
    "found_keywords": [...],
    "missing_keywords": [...],
    "final_cv": "...",
    "recommendations": [...],
    "improvements_applied": [...]
}}

IMPORTANTE: El campo "final_cv" debe contener el CV completo, optimizado y revisado, listo para enviar.""",
}


# ==================== AGENT CONFIGURATION ====================

AGENTS_CONFIG = {
    "cv_reviewer": {
        "name": "CV Reviewer",
        "description": "Analiza oferta, analiza CV, optimiza, evalúa ATS y revisa — todo en uno",
        "temperature": LLM_CONFIG["temperature_optimization"],
        "model": LLM_CONFIG["model"],
    },
}
