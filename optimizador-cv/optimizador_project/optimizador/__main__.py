"""
Interfaz CLI para el Optimizador de Currículums.
Punto de entrada: python -m optimizador
"""

import sys
import logging
from pathlib import Path

from optimizador.utils.pdf_loader import load_document
from optimizador.graph.workflow import create_workflow

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def print_header(title: str):
    """Imprime un encabezado formateado."""
    width = 70
    print("\n" + "=" * width)
    print(f" {title.center(width - 2)} ")
    print("=" * width + "\n")


def print_section(title: str):
    """Imprime un encabezado de sección."""
    print(f"\n📌 {title}")
    print("-" * 60)


def print_result(final_state) -> None:
    """Imprime los resultados del workflow."""
    
    print_header("RESULTADOS DE LA OPTIMIZACIÓN")
    
    # Verificar si hubo errores
    if final_state.errors:
        print("❌ ERRORES ENCONTRADOS:\n")
        for error in final_state.errors:
            print(f"  • {error}")
        return
    
    # Oferta matcheada
    if final_state.matched_offer_filename:
        print_section("🎯 Oferta Compatible Encontrada")
        print(f"  Oferta: {final_state.matched_offer_filename}")
        if final_state.offer_match_score:
            print(f"  Similitud: {final_state.offer_match_score * 100:.0f}%")
    
    # Puntuación ATS
    if final_state.ats_score:
        print_section("📊 PUNTUACIÓN ATS")
        score = final_state.ats_score
        print(f"  Puntuación Global: {score.overall_score:.0f}/100")
        print(f"  ├─ Keyword Match:    {score.keyword_match:.0f}%")
        print(f"  ├─ Formato:          {score.format_score:.0f}%")
        print(f"  └─ Completitud:      {score.completeness:.0f}%")
    
    # Keywords encontradas
    if final_state.found_keywords:
        print_section("✅ Keywords Encontradas")
        for kw in final_state.found_keywords[:10]:
            print(f"  ✓ {kw}")
        if len(final_state.found_keywords) > 10:
            print(f"  ... y {len(final_state.found_keywords) - 10} más")
    
    # Keywords faltantes
    if final_state.missing_keywords:
        print_section("❌ Keywords Faltantes")
        for kw in final_state.missing_keywords[:10]:
            print(f"  ✗ {kw}")
        if len(final_state.missing_keywords) > 10:
            print(f"  ... y {len(final_state.missing_keywords) - 10} más")
    
    # Cambios realizados
    if final_state.changes_made:
        print_section("📝 Cambios Realizados")
        for i, change in enumerate(final_state.changes_made, 1):
            print(f"  {i}. {change}")
    
    # Mejoras aplicadas en revisión final
    if final_state.improvements_applied:
        print_section("🔧 Mejoras Aplicadas en Revisión Final")
        for i, improvement in enumerate(final_state.improvements_applied, 1):
            print(f"  {i}. {improvement}")
    
    # Recomendaciones
    if final_state.ats_recommendations:
        print_section("💡 Recomendaciones Finales")
        for i, rec in enumerate(final_state.ats_recommendations, 1):
            print(f"  {i}. {rec}")
    
    # CV Final (primeros 500 caracteres)
    if final_state.final_cv:
        print_section("📄 Vista Previa del CV Final")
        preview = final_state.final_cv[:500].replace("\n", " ")
        print(f"  {preview}...")
        print(f"\n  [CV completo: {len(final_state.final_cv)} caracteres]")
    
    # Estadísticas
    print_section("📈 Estadísticas")
    print(f"  Match Score: {final_state.match_score:.1f}%")
    print(f"  Keywords añadidas: {len(final_state.keywords_added)}")
    print(f"  Total de cambios: {len(final_state.changes_made)}")
    
    print_header("FIN DE RESULTADOS")


def get_file_path(prompt: str, file_type: str = "documento") -> str:
    """
    Solicita al usuario una ruta de archivo válida.
    
    Args:
        prompt: Mensaje a mostrar
        file_type: Tipo de archivo esperado
        
    Returns:
        Ruta válida del archivo
    """
    while True:
        path_input = input(f"\n{prompt}: ").strip()
        
        if not path_input:
            print(f"❌ Por favor ingresa una ruta válida.")
            continue
        
        path = Path(path_input)
        
        if not path.exists():
            print(f"❌ El archivo no existe: {path}")
            continue
        
        if not path.is_file():
            print(f"❌ No es un archivo: {path}")
            continue
        
        return str(path)


def get_text_input(prompt: str) -> str:
    """
    Solicita texto al usuario (permite múltiples líneas).
    
    Args:
        prompt: Mensaje a mostrar
        
    Returns:
        Texto ingresado por el usuario
    """
    print(f"\n{prompt}")
    print("(Ingresa el texto y presiona Ctrl+D cuando termines, o Ctrl+Z+Enter en Windows)")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    return "\n".join(lines)


def main():
    """Función principal del CLI."""
    print_header("🚀 OPTIMIZADOR INTELIGENTE DE CURRÍCULUMS")
    
    print("Este sistema analizará tu CV, buscará la oferta más compatible")
    print("y lo optimizará automáticamente usando inteligencia artificial.\n")
    
    # Solicitar CV
    print("=" * 60)
    print("CARGAR CURRÍCULUM")
    print("=" * 60)
    print("El CV puede ser un archivo PDF o texto plano.")
    
    cv_path = get_file_path("Ruta al archivo de CV (PDF o TXT)", "CV")
    
    try:
        cv_text = load_document(cv_path)
        print(f"✅ CV cargado exitosamente ({len(cv_text)} caracteres)")
    except Exception as e:
        print(f"❌ Error cargando CV: {str(e)}")
        return 1
    
    # Ejecutar workflow (match + optimización)
    print("\n" + "=" * 60)
    print("PROCESANDO...")
    print("=" * 60)
    print("\n⏳ Buscando oferta compatible...")
    print("⏳ Analizando y optimizando CV...")
    print("⏳ Evaluando compatibilidad ATS...\n")
    
    try:
        workflow = create_workflow()
        final_state = workflow.invoke(cv_text)
        
        # Mostrar resultados
        print_result(final_state)
        
        # Opción de guardar CV optimizado
        if final_state.final_cv:
            save_choice = input("\n¿Deseas guardar el CV optimizado? (s/n): ").strip().lower()
            if save_choice == "s":
                output_path = input("Ruta para guardar el CV (ej: cv_optimizado.txt): ").strip()
                if output_path:
                    try:
                        with open(output_path, "w", encoding="utf-8") as f:
                            f.write(final_state.final_cv)
                        print(f"✅ CV guardado en: {output_path}")
                    except Exception as e:
                        print(f"❌ Error guardando archivo: {str(e)}")
        
        return 0
    
    except Exception as e:
        logger.error(f"Error en workflow: {str(e)}", exc_info=True)
        print(f"\n❌ Error durante el procesamiento: {str(e)}")
        print("\nVerifica que:")
        print("  • Ollama esté corriendo: ollama serve")
        print("  • Tienes qwen3:8b descargado: ollama pull qwen3:8b")
        print("  • Tienes nomic-embed-text descargado: ollama pull nomic-embed-text")
        return 1


if __name__ == "__main__":
    sys.exit(main())
