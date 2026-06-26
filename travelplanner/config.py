import os

# URL base de Ollama. En Docker apunta al servicio interno; en local usa localhost.
OLLAMA_URL = os.getenv("OLLAMA_API_BASE_URL", "http://localhost:11434")

# Modelo LLM a usar. Cambia OLLAMA_MODEL en .env para usar otro modelo.
# Ejemplos: qwen3:1.7b | qwen3:4b | llama3.2:3b | mistral:7b
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:1.7b")
