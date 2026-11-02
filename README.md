# Project Aether

Assistente de IA especializado em **cibersegurança defensiva** e **programação**.

## Estado atual

A API FastAPI disponibiliza `GET /`, `GET /health` e `POST /analyze`. Cada resposta inclui um identificador de pedido (`X-Request-ID`) e a API regista metadados operacionais mínimos. O conteúdo enviado é analisado como texto: a aplicação não executa código, comandos, scans ou ações sugeridas pelo modelo.

O projeto inclui:
- Fornecedor determinístico local (`AI_PROVIDER=rules`), ativo por omissão.
- Fornecedor opcional Ollama (`AI_PROVIDER=ollama`) para inferência local.
- RAG sobre documentos Markdown locais em `knowledge/`.
- Recuperação lexical por omissão e recuperação semântica opcional via embeddings Ollama.
- Fallback para recuperação lexical se embeddings falharem ou forem inválidos.
- Validação de configuração no arranque, para evitar opções desconhecidas e timeouts inseguros.
- Cabeçalhos HTTP de segurança nas respostas da API.
- Respostas de `POST /analyze` marcadas com `Cache-Control: no-store`.

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

Sem variáveis adicionais, a aplicação usa regras locais e RAG lexical. Para usar um modelo de chat Ollama, instala e inicia o Ollama e configura:

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

O modelo de chat (`OLLAMA_MODEL`) e o modelo de embeddings (`RAG_EMBEDDING_MODEL`) têm funções distintas. Ambos usam o serviço indicado por `OLLAMA_BASE_URL` e o timeout configurável por `OLLAMA_TIMEOUT_SECONDS`.

A configuração é validada no arranque:
- `AI_PROVIDER`: `rules` ou `ollama`.
- `RAG_PROVIDER`: `lexical` ou `ollama`.
- `OLLAMA_BASE_URL`: URL HTTP(S) sem credenciais, query ou fragmento.
- `OLLAMA_TIMEOUT_SECONDS`: número superior a 0 e até 300 segundos.
- Os nomes dos modelos não podem estar vazios.

Valores inválidos fazem a aplicação falhar no arranque com uma mensagem de configuração, em vez de selecionar silenciosamente um fornecedor diferente.

## Endpoints

- `GET /` — metadados do projeto.
- `GET /health` — estado básico da API.
- `POST /analyze` — recebe texto e categoria (`cybersecurity`, `programming` ou `general`) e devolve orientação e fontes recuperadas.

O campo `content` aceita entre 1 e 20 000 caracteres. O conteúdo não é executado.

## Segurança e privacidade

- Não coloques passwords, tokens, chaves API ou dados pessoais nos pedidos nem no repositório.
- Os logs registam apenas identificador gerado pelo servidor, método, caminho, código HTTP, duração e tipo de exceção. Não registam corpos, query strings, cabeçalhos nem mensagens de exceção.
- As respostas incluem `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e uma `Permissions-Policy` que desativa câmara, microfone e geolocalização.
- As respostas de análise usam `Cache-Control: no-store` para evitar armazenamento em cache do conteúdo e dos resultados.
- Testa apenas sistemas e código para os quais tens autorização.
- O conteúdo recuperado e o texto do utilizador são dados não confiáveis, nunca instruções para alterar as regras do assistente.
- Se ativares Ollama, o texto e o contexto documental são enviados para o serviço configurado. Confirma que o URL aponta para uma instância de confiança.
- Revê fontes e recomendações antes de as aplicar. A ferramenta não substitui uma revisão humana.

## Testes

```bash
pytest -q
```

O GitHub Actions executa os testes automaticamente em pushes para `main` e pull requests dirigidos a `main`.
