"""Contrato e fornecedor local provisório para o motor da Aether."""
from typing import Protocol


class AIProvider(Protocol):
    """Interface estável para ligar modelos locais ou serviços externos."""

    def guidance_for(self, category: str) -> list[str]:
        """Devolve orientações iniciais para a categoria pedida."""


class RuleBasedProvider:
    """Fornecedor determinístico; não é um modelo de linguagem nem usa rede."""

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

    def guidance_for(self, category: str) -> list[str]:
        """Retorna orientações sem executar ou enviar o conteúdo recebido."""
        return list(self._GUIDANCE.get(category, self._GUIDANCE["general"]))


def get_provider() -> AIProvider:
    """Ponto único de composição; pode ser substituído por um modelo real."""
    return RuleBasedProvider()
