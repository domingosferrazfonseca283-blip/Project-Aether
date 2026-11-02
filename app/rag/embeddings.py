"""Adaptador de embeddings para uma instância Ollama local."""
import httpx

from app.core.config import Settings


class OllamaEmbeddingError(RuntimeError):
    """Erro controlado ao obter embeddings do serviço Ollama local."""


class OllamaEmbedder:
    """Obtém vetores através do endpoint local /api/embed."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not texts or any(not isinstance(item, str) or not item.strip() for item in texts):
            raise OllamaEmbeddingError("Os textos para embedding não podem estar vazios.")

        payload = {"model": self.settings.rag_embedding_model, "input": texts}
        try:
            with httpx.Client(timeout=self.settings.ollama_timeout_seconds) as client:
                response = client.post(
                    f"{self.settings.ollama_base_url}/api/embed", json=payload
                )
                response.raise_for_status()
                embeddings = response.json()["embeddings"]
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise OllamaEmbeddingError(
                "Não foi possível obter embeddings do modelo local."
            ) from exc

        if (
            not isinstance(embeddings, list)
            or len(embeddings) != len(texts)
            or any(
                not isinstance(vector, list)
                or not vector
                or any(not isinstance(value, (int, float)) for value in vector)
                for vector in embeddings
            )
        ):
            raise OllamaEmbeddingError("O modelo local devolveu embeddings inválidos.")

        return [[float(value) for value in vector] for vector in embeddings]
