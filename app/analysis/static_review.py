"""Regras heurísticas para revisão estática de código como texto; nunca executa entrada."""
from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class Finding:
    rule_id: str
    severity: str
    line: int
    message: str
    recommendation: str


_RULES = (
    (
        "PY001", "high", re.compile(r"\beval\s*\("),
        "Uso de eval pode executar expressões dinâmicas.",
        "Evita eval; usa parsing e operações explicitamente permitidas.",
    ),
    (
        "PY002", "high", re.compile(r"\bexec\s*\("),
        "Uso de exec pode executar código dinâmico.",
        "Substitui execução dinâmica por funções e fluxos explícitos.",
    ),
    (
        "PY003", "high", re.compile(r"\bpickle\.(?:loads|load)\s*\("),
        "Desserialização pickle de dados não confiáveis pode executar código.",
        "Não desserializes pickle não confiável; prefere formatos de dados simples.",
    ),
    (
        "PY004", "high", re.compile(r"\byaml\.load\s*\("),
        "yaml.load pode construir objetos não seguros dependendo do loader.",
        "Usa yaml.safe_load para dados não confiáveis e valida o esquema.",
    ),
    (
        "PY005", "high", re.compile(r"\bsubprocess\.(?:run|Popen|call|check_output)\s*\([^\n]*\bshell\s*=\s*True"),
        "Execução de subprocesso com shell=True aumenta o risco de injeção.",
        "Evita shell=True; passa argumentos numa lista e valida os valores.",
    ),
    (
        "PY006", "medium", re.compile(r"(?i)(?:api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]"),
        "Possível segredo literal no código.",
        "Remove o segredo do código e utiliza um gestor de segredos ou variável de ambiente.",
    ),
    (
        "PY007", "medium", re.compile(r"\b(?:requests\.(?:get|post)|httpx\.(?:get|post))\s*\([^\n]*verify\s*=\s*False"),
        "A validação TLS parece estar desativada.",
        "Mantém a verificação de certificados TLS ativa e configura uma CA confiável.",
    ),
)


def review_code(source: str) -> list[dict[str, object]]:
    """Analisa linhas com padrões conhecidos; não importa, compila ou executa o texto."""
    if not isinstance(source, str) or not source.strip():
        raise ValueError("O código a rever não pode estar vazio.")
    if len(source) > 20_000:
        raise ValueError("O código excede o limite de 20 000 caracteres.")

    findings: list[Finding] = []
    for line_number, line in enumerate(source.splitlines(), start=1):
        stripped = line.lstrip()
        if stripped.startswith(("#", "//", "/*", "*")):
            continue
        for rule_id, severity, pattern, message, recommendation in _RULES:
            if pattern.search(line):
                findings.append(
                    Finding(rule_id, severity, line_number, message, recommendation)
                )
    return [asdict(item) for item in findings]
