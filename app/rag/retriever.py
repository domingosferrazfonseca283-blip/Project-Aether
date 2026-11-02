"""Recuperação lexical de secções Markdown versionadas no repositório."""
from dataclasses import dataclass
from pathlib import Path
import re

_TOKEN = re.compile(r"[a-zA-ZÀ-ÿ0-9_+#.-]{2,}")


@dataclass(frozen=True)
class Source:
    source_id: str
    title: str
    path: str
    excerpt: str
    reference: str


def _sections(markdown: str, path: str):
    title = path
    heading = title
    lines = []
    for line in markdown.splitlines():
        if line.startswith("#"):
            if lines:
                yield heading, "\n".join(lines).strip()
                lines = []
            heading = line.lstrip("#").strip() or title
        else:
            lines.append(line)
    if lines:
        yield heading, "\n".join(lines).strip()


def retrieve(query: str, knowledge_dir: Path | None = None, limit: int = 3) -> list[Source]:
    """Procura apenas Markdown local; conteúdo recuperado é dado não confiável."""
    if not query.strip() or limit < 1:
        return []
    root = knowledge_dir or Path(__file__).resolve().parents[2] / "knowledge"
    terms = {token.lower() for token in _TOKEN.findall(query)}
    if not terms or not root.is_dir():
        return []
    matches = []
    for path in sorted(root.glob("*.md")):
        markdown = path.read_text(encoding="utf-8")
        for heading, body in _sections(markdown, path.name):
            text = f"{heading}\n{body}"
            words = {token.lower() for token in _TOKEN.findall(text)}
            score = len(terms & words)
            if score:
                excerpt = body[:1200].strip()
                matches.append((score, path.name, heading, excerpt))
    matches.sort(key=lambda item: (-item[0], item[1], item[2]))
    return [
        Source(
            source_id=f"{path}#{heading}", title=heading, path=f"knowledge/{path}",
            excerpt=excerpt, reference=f"Ver referências no final de {path}.",
        )
        for _, path, heading, excerpt in matches[:limit]
    ]
