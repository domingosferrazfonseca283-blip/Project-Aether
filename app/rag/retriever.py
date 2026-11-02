"""Recuperação lexical ou semântica de secções Markdown locais."""
from dataclasses import dataclass
from math import isfinite, sqrt
from pathlib import Path
import re
from typing import Protocol

_TOKEN = re.compile(r"[a-zA-ZÀ-ÿ0-9_+#.-]{2,}")


class Embedder(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    path: str
    excerpt: str
    reference: str


def _sections(markdown: str, path: str):
    heading, lines = path, []
    for line in markdown.splitlines():
        if line.startswith("#"):
            body = "\n".join(lines).strip()
            if body:
                yield heading, body
            lines = []
            heading = line.lstrip("#").strip() or path
        else:
            lines.append(line)
    body = "\n".join(lines).strip()
    if body:
        yield heading, body


def _documents(root: Path) -> list[tuple[str, str, str]]:
    return [
        (path.name, heading, body)
        for path in sorted(root.glob("*.md"))
        for heading, body in _sections(path.read_text(encoding="utf-8"), path.name)
    ]


def _source(item: tuple[str, str, str]) -> Source:
    path, heading, body = item
    return Source(
        f"{path}#{heading}", heading, f"knowledge/{path}", body[:1200].strip(),
        f"Ver referências no final de {path}.",
    )


def _validate_vectors(vectors: list[list[float]], expected: int) -> None:
    if not isinstance(vectors, list) or len(vectors) != expected:
        raise ValueError("Quantidade inesperada de embeddings")
    if any(
        not isinstance(vector, list)
        or not vector
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            for value in vector
        )
        for vector in vectors
    ):
        raise ValueError("Embeddings inválidos")
    if len({len(vector) for vector in vectors}) != 1:
        raise ValueError("Dimensões incompatíveis nos embeddings")


def _cosine(a: list[float], b: list[float]) -> float:
    na, nb = sqrt(sum(x * x for x in a)), sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / (na * nb) if na and nb else 0.0


def retrieve(
    query: str,
    knowledge_dir: Path | None = None,
    limit: int = 3,
    embedder: Embedder | None = None,
) -> list[Source]:
    """Procura apenas Markdown local; documentos são dados não confiáveis."""
    if not query.strip() or limit < 1:
        return []
    root = knowledge_dir or Path(__file__).resolve().parents[2] / "knowledge"
    if not root.is_dir():
        return []
    docs = _documents(root)
    if not docs:
        return []
    if embedder is not None:
        vectors = embedder.embed([query] + [f"{h}\n{b}" for _, h, b in docs])
        _validate_vectors(vectors, len(docs) + 1)
        ranked = sorted(
            ((_cosine(vectors[0], vector), doc) for vector, doc in zip(vectors[1:], docs)),
            key=lambda item: (-item[0], item[1][0], item[1][1]),
        )
        return [_source(doc) for score, doc in ranked[:limit] if score > 0]

    terms = {token.lower() for token in _TOKEN.findall(query)}
    ranked = []
    for doc in docs:
        words = {token.lower() for token in _TOKEN.findall(f"{doc[1]}\n{doc[2]}")}
        score = len(terms & words)
        if score:
            ranked.append((score, doc))
    ranked.sort(key=lambda item: (-item[0], item[1][0], item[1][1]))
    return [_source(doc) for _, doc in ranked[:limit]]
