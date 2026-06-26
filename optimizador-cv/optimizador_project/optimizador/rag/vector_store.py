"""
Sistema RAG (Retrieval-Augmented Generation) usando ChromaDB.
Carga documentos, genera embeddings y permite búsqueda vectorial.
"""

import logging
from pathlib import Path
from typing import List, Optional
import json

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from optimizador.config import RAG_CONFIG, DOCS_DIR

logger = logging.getLogger(__name__)


class CVKnowledgeBase:
    """Gestiona la base de conocimiento vectorial para CV optimization."""
    
    def __init__(self, force_rebuild: bool = False):
        """
        Inicializa la base de conocimiento.
        
        Args:
            force_rebuild: Si es True, reconstruye la base desde documentos
        """
        self.config = RAG_CONFIG
        self.embedding_function = None
        self.vector_store = None
        
        try:
            self._initialize_embeddings()
            self._initialize_vector_store(force_rebuild)
        except Exception as e:
            logger.error(f"Error inicializando Knowledge Base: {str(e)}")
            raise
    
    def _initialize_embeddings(self):
        """Inicializa el modelo de embeddings de Ollama."""
        try:
            self.embedding_function = OllamaEmbeddings(
                model=self.config["embedding_model"],
                base_url=RAG_CONFIG.get("base_url", "http://localhost:11434"),
            )
            logger.info(f"Embeddings inicializados: {self.config['embedding_model']}")
        except Exception as e:
            logger.error(f"Error al inicializar embeddings: {str(e)}")
            raise RuntimeError(
                f"No se pudo conectar a Ollama para embeddings. "
                f"Verifica que Ollama está corriendo y que tienes 'ollama pull {self.config['embedding_model']}' descargado."
            )
    
    def _initialize_vector_store(self, force_rebuild: bool = False):
        """
        Inicializa o carga la base de datos vectorial.
        
        Args:
            force_rebuild: Si es True, reconstruye desde cero
        """
        persist_dir = Path(self.config["persist_directory"])
        
        if force_rebuild or not self._is_database_initialized(persist_dir):
            logger.info("Construyendo base de conocimiento desde documentos...")
            self._load_documents_and_build_index(persist_dir)
        else:
            logger.info(f"Cargando base de conocimiento existente: {persist_dir}")
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
    
    def _is_database_initialized(self, persist_dir: Path) -> bool:
        """Verifica si la base de datos ya existe."""
        if not persist_dir.exists():
            return False
        
        # Verifica si hay archivos de ChromaDB
        chroma_files = list(persist_dir.glob("*.db"))
        return len(chroma_files) > 0
    
    def _load_documents_and_build_index(self, persist_dir: Path):
        """Carga documentos desde docs/ y construye el índice vectorial."""
        all_documents = []
        
        # Cargar documentos de la carpeta docs/
        doc_files = list(DOCS_DIR.glob("*.txt")) + list(DOCS_DIR.glob("*.md"))
        
        if not doc_files:
            logger.warning(f"No se encontraron documentos en {DOCS_DIR}")
            # Crear una base de datos vacía pero funcional
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            return
        
        logger.info(f"Cargando {len(doc_files)} documentos de {DOCS_DIR}")
        
        for file_path in doc_files:
            try:
                if file_path.suffix == ".txt":
                    loader = TextLoader(str(file_path), encoding="utf-8")
                elif file_path.suffix == ".md":
                    loader = TextLoader(str(file_path), encoding="utf-8")
                else:
                    continue
                
                documents = loader.load()
                logger.info(f"Cargado: {file_path.name} ({len(documents)} documentos)")
                all_documents.extend(documents)
                
            except Exception as e:
                logger.warning(f"Error cargando {file_path.name}: {str(e)}")
                continue
        
        if not all_documents:
            logger.warning("No se pudieron cargar documentos válidos")
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            return
        
        # Dividir documentos en chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config["chunk_size"],
            chunk_overlap=self.config["chunk_overlap"],
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
        chunks = text_splitter.split_documents(all_documents)
        logger.info(f"Documentos divididos en {len(chunks)} chunks")
        
        # Crear índice vectorial
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_function,
            collection_name=self.config["collection_name"],
            persist_directory=str(persist_dir),
        )
        
        logger.info(f"Base de conocimiento creada exitosamente en {persist_dir}")
    
    def search(self, query: str, k: Optional[int] = None) -> List[str]:
        """
        Busca documentos relevantes para una consulta.
        
        Args:
            query: Pregunta o consulta de búsqueda
            k: Número de documentos a retornar (por defecto: config["top_k"])
            
        Returns:
            Lista de documentos relevantes como strings
        """
        if self.vector_store is None:
            logger.warning("Vector store no inicializado")
            return []
        
        k = k or self.config["top_k"]
        
        try:
            # Búsqueda por similitud
            results = self.vector_store.similarity_search(query, k=k)
            
            # Extrae el contenido de los documentos
            context = "\n\n".join([doc.page_content for doc in results])
            
            logger.info(f"Búsqueda '{query[:50]}...' encontró {len(results)} documentos")
            return [doc.page_content for doc in results]
            
        except Exception as e:
            logger.error(f"Error en búsqueda vectorial: {str(e)}")
            return []
    
    def get_context_for_query(self, query: str, k: Optional[int] = None) -> str:
        """
        Obtiene contexto formateado para usar en prompts.
        
        Args:
            query: Consulta de búsqueda
            k: Número de documentos
            
        Returns:
            Contexto formateado como string
        """
        results = self.search(query, k)
        
        if not results:
            return "No se encontró información relevante en la base de conocimiento."
        
        context = "### Información relevante de la base de conocimiento:\n\n"
        for i, doc in enumerate(results, 1):
            # Limita longitud del documento
            truncated = (doc[:300] + "...") if len(doc) > 300 else doc
            context += f"{i}. {truncated}\n\n"
        
        return context


# Singleton para reutilizar la instancia
_knowledge_base_instance: Optional[CVKnowledgeBase] = None


def get_knowledge_base(force_rebuild: bool = False) -> CVKnowledgeBase:
    """
    Obtiene la instancia global de la base de conocimiento.
    
    Args:
        force_rebuild: Si es True, reconstruye la base
        
    Returns:
        Instancia de CVKnowledgeBase
    """
    global _knowledge_base_instance
    
    if _knowledge_base_instance is None or force_rebuild:
        _knowledge_base_instance = CVKnowledgeBase(force_rebuild=force_rebuild)
    
    return _knowledge_base_instance


def reset_knowledge_base():
    """Reinicia la instancia global de la base de conocimiento."""
    global _knowledge_base_instance
    _knowledge_base_instance = None
