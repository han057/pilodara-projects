"""
Job Offer Store: Carga ofertas de empleo desde ofertas/ y las indexa en ChromaDB.
Permite buscar la oferta más compatible con un CV usando embeddings.
"""

import logging
from pathlib import Path
from typing import List, Optional, Dict

from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader, PyPDFLoader

from optimizador.config import OFERTAS_RAG_CONFIG, OFERTAS_DIR

logger = logging.getLogger(__name__)


class JobOfferStore:
    """Gestiona la indexación y búsqueda de ofertas de empleo en ChromaDB."""

    def __init__(self, force_rebuild: bool = False):
        self.config = OFERTAS_RAG_CONFIG
        self.embedding_function = None
        self.vector_store = None
        # Diccionario para guardar el texto completo de cada oferta
        self._offers_full_text: Dict[str, str] = {}

        try:
            self._initialize_embeddings()
            self._initialize_vector_store(force_rebuild)
        except Exception as e:
            logger.error(f"Error inicializando JobOfferStore: {str(e)}")
            raise

    def _initialize_embeddings(self):
        """Inicializa el modelo de embeddings de Ollama."""
        try:
            self.embedding_function = OllamaEmbeddings(
                model=self.config["embedding_model"],
                base_url=self.config.get("base_url", "http://localhost:11434"),
            )
            logger.info(f"Embeddings inicializados: {self.config['embedding_model']}")
        except Exception as e:
            logger.error(f"Error al inicializar embeddings: {str(e)}")
            raise RuntimeError(
                f"No se pudo conectar a Ollama para embeddings. "
                f"Verifica que Ollama está corriendo y que tienes "
                f"'ollama pull {self.config['embedding_model']}' descargado."
            )

    def _initialize_vector_store(self, force_rebuild: bool = False):
        """Inicializa o carga la colección de ofertas."""
        persist_dir = Path(self.config["persist_directory"])

        if force_rebuild or not self._is_database_initialized(persist_dir):
            logger.info("Construyendo índice de ofertas desde archivos...")
            self._load_offers_and_build_index(persist_dir)
        else:
            logger.info(f"Cargando índice de ofertas existente: {persist_dir}")
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            # Reconstruir diccionario de textos completos
            self._rebuild_full_text_dict()

    def _is_database_initialized(self, persist_dir: Path) -> bool:
        """Verifica si la colección ya existe."""
        if not persist_dir.exists():
            return False
        chroma_files = list(persist_dir.glob("*.db"))
        if len(chroma_files) == 0:
            return False
        # Verificar si la colección específica existe
        try:
            test_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            return test_store._collection.count() > 0
        except Exception:
            return False

    def _load_offers_and_build_index(self, persist_dir: Path):
        """Carga ofertas desde ofertas/ y construye el índice."""
        all_documents: List[Document] = []

        # Buscar archivos .txt y .pdf en OFERTAS_DIR
        offer_files = list(OFERTAS_DIR.glob("*.txt")) + list(OFERTAS_DIR.glob("*.pdf"))

        if not offer_files:
            logger.warning(f"No se encontraron ofertas en {OFERTAS_DIR}")
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            return

        logger.info(f"Cargando {len(offer_files)} ofertas de {OFERTAS_DIR}")

        for file_path in offer_files:
            try:
                if file_path.suffix == ".txt":
                    loader = TextLoader(str(file_path), encoding="utf-8")
                elif file_path.suffix == ".pdf":
                    loader = PyPDFLoader(str(file_path))
                else:
                    continue

                documents = loader.load()
                # Combinar todas las páginas en un solo texto (oferta completa)
                full_text = "\n".join([doc.page_content for doc in documents])

                # Guardar texto completo en diccionario
                filename = file_path.stem
                self._offers_full_text[filename] = full_text

                # Crear un documento único por oferta (sin chunk)
                offer_doc = Document(
                    page_content=full_text,
                    metadata={
                        "source": str(file_path),
                        "filename": filename,
                    },
                )
                all_documents.append(offer_doc)
                logger.info(f"Oferta cargada: {file_path.name} ({len(full_text)} chars)")

            except Exception as e:
                logger.warning(f"Error cargando oferta {file_path.name}: {str(e)}")
                continue

        if not all_documents:
            logger.warning("No se pudieron cargar ofertas válidas")
            self.vector_store = Chroma(
                collection_name=self.config["collection_name"],
                embedding_function=self.embedding_function,
                persist_directory=str(persist_dir),
            )
            return

        # Crear índice vectorial (una oferta = un vector)
        self.vector_store = Chroma.from_documents(
            documents=all_documents,
            embedding=self.embedding_function,
            collection_name=self.config["collection_name"],
            persist_directory=str(persist_dir),
        )

        logger.info(
            f"Índice de ofertas creado: {len(all_documents)} ofertas en {persist_dir}"
        )

    def _rebuild_full_text_dict(self):
        """Reconstruye el diccionario de textos completos desde la colección."""
        if self.vector_store is None:
            return
        try:
            collection = self.vector_store._collection
            all_items = collection.get()
            if all_items and all_items.get("documents"):
                for i, doc_text in enumerate(all_items["documents"]):
                    metadata = all_items.get("metadatas", [{}])[i] if all_items.get("metadatas") else {}
                    filename = metadata.get("filename", f"offer_{i}")
                    self._offers_full_text[filename] = doc_text
            logger.info(f"Diccionario de ofertas reconstruido: {len(self._offers_full_text)} ofertas")
        except Exception as e:
            logger.warning(f"No se pudo reconstruir diccionario de ofertas: {e}")

    def match_best_offer(self, cv_text: str) -> Optional[Dict]:
        """
        Busca la oferta más compatible con el CV usando similitud de embeddings.

        Args:
            cv_text: Texto completo del CV del candidato

        Returns:
            Dict con "offer_text", "offer_filename", "similarity_score"
            o None si no hay ofertas disponibles
        """
        if self.vector_store is None:
            logger.warning("Vector store de ofertas no inicializado")
            return None

        try:
            results = self.vector_store.similarity_search_with_relevance_scores(
                cv_text, k=self.config["top_k"]
            )

            if not results:
                logger.warning("No se encontraron ofertas compatibles")
                return None

            best_doc, score = results[0]
            filename = best_doc.metadata.get("filename", "unknown")
            offer_text = self._offers_full_text.get(filename, best_doc.page_content)

            logger.info(
                f"Oferta matcheada: {filename} (similitud: {score:.3f})"
            )

            return {
                "offer_text": offer_text,
                "offer_filename": filename,
                "similarity_score": round(score, 3),
            }

        except Exception as e:
            logger.error(f"Error buscando oferta compatible: {str(e)}")
            return None

    def list_offers(self) -> List[Dict]:
        """Lista todas las ofertas indexadas con metadata parseada."""
        offers = []
        for filename, text in sorted(self._offers_full_text.items()):
            meta = self._parse_metadata(text)
            meta["filename"] = filename
            offers.append(meta)
        return offers

    def get_offer_text(self, filename: str) -> Optional[str]:
        """Obtiene el texto completo de una oferta por su filename."""
        return self._offers_full_text.get(filename)

    @staticmethod
    def _parse_metadata(text: str) -> Dict:
        """Parsea metadata (título, empresa, ubicación, salario) del texto de la oferta."""
        meta = {"title": "", "company": "", "location": "", "salary": ""}
        for line in text.split("\n")[:6]:
            line = line.strip()
            if line.lower().startswith("título:"):
                meta["title"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("empresa:"):
                meta["company"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("ubicación:"):
                meta["location"] = line.split(":", 1)[1].strip()
            elif line.lower().startswith("salario:"):
                meta["salary"] = line.split(":", 1)[1].strip()
        return meta


# Singleton
_offer_store_instance: Optional[JobOfferStore] = None


def get_offer_store(force_rebuild: bool = False) -> JobOfferStore:
    """Obtiene la instancia global del store de ofertas."""
    global _offer_store_instance
    if _offer_store_instance is None or force_rebuild:
        _offer_store_instance = JobOfferStore(force_rebuild=force_rebuild)
    return _offer_store_instance


def reset_offer_store():
    """Reinicia la instancia global del store de ofertas."""
    global _offer_store_instance
    _offer_store_instance = None
