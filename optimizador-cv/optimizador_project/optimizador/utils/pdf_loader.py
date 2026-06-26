"""
Utilidades para cargar archivos PDF y extraer texto.
"""

from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


def load_pdf_text(file_path: str) -> str:
    """
    Carga un archivo PDF y extrae todo el texto.
    
    Args:
        file_path: Ruta al archivo PDF
        
    Returns:
        Texto extraído del PDF
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si no se puede leer el PDF
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo {file_path} no existe")
    
    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"El archivo debe ser un PDF, se recibió: {file_path.suffix}")
    
    try:
        # Intentar con PyPDFLoader de LangChain
        from langchain_community.document_loaders import PyPDFLoader
        
        loader = PyPDFLoader(str(file_path))
        pages = loader.load()
        
        if not pages:
            logger.warning(f"El PDF {file_path} está vacío o no se pudo extraer texto")
            return ""
        
        text = "\n".join([page.page_content for page in pages])
        logger.info(f"PDF cargado exitosamente: {file_path} ({len(pages)} páginas)")
        return text
        
    except ImportError:
        logger.error("PyPDF no está instalado. Instala: pip install pypdf langchain-community")
        raise
    except Exception as e:
        logger.error(f"Error al cargar PDF {file_path}: {str(e)}")
        raise ValueError(f"No se pudo extraer texto del PDF: {str(e)}")


def load_text_file(file_path: str) -> str:
    """
    Carga un archivo de texto plano.
    
    Args:
        file_path: Ruta al archivo de texto
        
    Returns:
        Contenido del archivo
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"El archivo {file_path} no existe")
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        logger.info(f"Archivo de texto cargado: {file_path}")
        return content
    except Exception as e:
        logger.error(f"Error al cargar archivo de texto {file_path}: {str(e)}")
        raise


def load_document(file_path: str) -> str:
    """
    Carga un documento (PDF o texto) automáticamente según extensión.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Contenido del documento
    """
    file_path = Path(file_path)
    
    if file_path.suffix.lower() == ".pdf":
        return load_pdf_text(str(file_path))
    elif file_path.suffix.lower() in [".txt", ".md"]:
        return load_text_file(str(file_path))
    else:
        raise ValueError(f"Formato de archivo no soportado: {file_path.suffix}")
