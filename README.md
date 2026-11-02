# Project Aether

Assistente de IA especializado em **cibersegurança defensiva** e **programação**.

## Estado atual

A API FastAPI disponibiliza `GET /`, `GET /health` e `POST /analyze`. O conteúdo enviado é analisado como texto: a aplicação não executa código, comandos, scans ou ações sugeridas pelo modelo.

O projeto inclui:
- Fornecedor determinístico local (`AI_PROVIDER=rules`), ativo por omissão.
- Fornecedor opcional Ollama (`AI_PROVIDER=ollama`) para inferência local.
- RAG sobre documentos Markdown locais em `knowledge/`.
- Recuperação lexical por omissão e recuperação semântica opcional via embeddings Ollama.
- Fallback automático para recuperação lexical se o serviço de embeddings falhar ou devolver dados inválidos.

## Requisitos e instalação

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

A documentação interativa fica disponível em http://127.0.0.1:8000/docs.

## Configuração

Sem variáveis adicionais, a aplicação usa regras locais e RAG lexical. Para usar um modelo de chat Ollama, instala e inicia o Ollama localmente e configura:

```bash
# Linux/macOS
export AI_PROVIDER=ollama
export OLLAMA_MODEL=qwen2.5:3b
export OLLAMA_BASE_URL=http://127.0.0.1:11434

# Windows PowerShell
$env:AI_PROVIDER="ollama"
$env:OLLAMA_MODEL="qwen2.5:3b"
$env:OLLAMA_BASE_URL="http://127.0.0.1:11434"
```

Para ativar recuperação semântica, configura separadamente o modelo de embeddings:

```bash
# Linux/macOS
export RAG_PROVIDER=ollama
export RAG_EMBEDDING_MODEL=nomic-embed-text

# Windows PowerShell
$env:RAG_PROVIDER="ollama"
$env:RAG_EMBEDDING_MODEL="nomic-embed-text"
```

O modelo de chat (`OLLAMA_MODEL`) e o modelo de embeddings (`RAG_EMBEDDING_MODEL`) têm funções distintas. Ambos usam o serviço local indicado por `OLLAMA_BASE_URL` e o timeout configurável por `OLLAMA_TIMEOUT_SECONDS`.

A recuperação semântica envia a consulta e as secções documentais locais para o endpoint Ollama `/api/embed`. Se a chamada falhar ou os vetores forem inválidos, a API regressa à recuperação lexical. A inferência de chat usa `/api/chat`; se esse serviço falhar, a API devolve HTTP 503.

## Endpoints

- `GET /` — metadados do projeto.
- `GET /health` — estado básico da API.
- `POST /analyze` — recebe texto e categoria (`cybersecurity`, `programming` ou `general`) e devolve orientação e fontes recuperadas.

O campo `content` aceita entre 1 e 20 000 caracteres. O conteúdo não é executado.

## Segurança e privacidade

- Não coloques passwords, tokens, chaves API ou dados pessoais nos pedidos nem no repositório.
- Testa apenas sistemas e código para os quais tens autorização.
- O conteúdo recuperado e o texto do utilizador são dados não confiáveis, nunca instruções para alterar as regras do assistente.
- Se ativares Ollama, o texto e o contexto documental são enviados para o serviço local configurado.
- Revê fontes e recomendações antes de as aplicar. A ferramenta não substitui uma revisão humana.

## Testes

```bash
pytest -q
```

O GitHub Actions executa os testes automaticamente em pushes para `main` e pull requests dirigidos a `main`.
