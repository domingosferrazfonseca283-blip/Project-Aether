# Project Aether

Assistente de IA especializado em **cibersegurança defensiva** e **programação**.

## Objetivos
- Explicar conceitos de segurança, vulnerabilidades e CVEs.
- Ajudar a rever código e identificar práticas inseguras.
- Apoiar debugging e desenvolvimento em Python.
- Consultar documentação própria através de RAG numa fase posterior.

## Estado
Fase inicial: estrutura base da API. Ainda não existe modelo treinado nem integração com um fornecedor de IA.

## Começar
Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir a documentação interativa em http://127.0.0.1:8000/docs.

## Endpoints
- `GET /` — informações do projeto.
- `GET /health` — estado da API.
- `POST /analyze` — análise inicial de texto/código; nesta fase devolve orientações estruturadas, sem executar o conteúdo enviado.

## Segurança
- Não colocar tokens, passwords ou chaves API no repositório.
- Usar variáveis de ambiente e um ficheiro local `.env` (ignorado pelo Git).
- Testar apenas sistemas e código para os quais tens autorização.

## Testes

Instala as dependências e executa os testes automatizados com:

```bash
pytest -q
```

O GitHub Actions executa esta suite automaticamente em cada push para `main` e em pull requests dirigidos a `main`.

## Próximas etapas
1. Definir a interface de um fornecedor/modelo de IA sem prender o projeto a um único serviço.
2. Implementar recuperação de documentação (RAG) com fontes verificáveis.
3. Adicionar testes de segurança, limites de entrada e registos sem dados sensíveis.


## Motor de IA (fase atual)

A API usa uma interface `AIProvider` em `app/ai/provider.py`. O fornecedor ativo é `RuleBasedProvider`, um placeholder local e determinístico que fornece orientações por categoria. **Ainda não é um LLM e não envia dados para serviços externos.**

Esta separação permite integrar futuramente um modelo local ou um fornecedor externo sem acoplar a API à implementação. Antes dessa integração serão definidos gestão segura de credenciais, limites de utilização, proteção de dados e testes.
