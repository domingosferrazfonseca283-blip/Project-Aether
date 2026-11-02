"""Contrato e fornecedor determinístico de fallback."""
from typing import Protocol


class AIProvider(Protocol):
    name: str

    def analyze(self, content: str, category: str, context: str = "") -> list[str]:
        """Analisa texto e contexto documental sem executar código."""


class RuleBasedProvider:
    """Fornecedor local determinístico; não é um modelo de linguagem."""

    name = "rule_based"

    _GUIDANCE = {
        "cybersecurity": [
            "Define o ativo e o objetivo da avaliação antes de começar.",
            "Testa apenas sistemas próprios ou para os quais tens autorização explícita.",
            "Prioriza mitigação, atualização e validação em ambiente controlado.",
        ],
        "programming": [
            "Partilha a mensagem de erro e o comportamento esperado, sem incluir segredos.",
            "Divide o problema em passos pequenos e cria testes reproduzíveis.",
            "Revê validação de entradas, tratamento de erros e dependências.",
        ],
        "general": [
            "Descreve o objetivo, o contexto e o resultado que esperas obter.",
            "Remove passwords, tokens, dados pessoais e outros segredos antes de partilhar.",
            "Pede explicações e exemplos pequenos que possas verificar.",
        ],
    }

    def analyze(self, content: str, category: str, context: str = "") -> list[str]:
        """Devolve orientações sem enviar o conteúdo para fora do processo."""
        return list(self._GUIDANCE.get(category, self._GUIDANCE["general"]))
