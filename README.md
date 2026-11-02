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
