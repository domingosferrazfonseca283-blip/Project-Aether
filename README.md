# Kamba

> Nome anterior do projeto: Project Aether. O repositório GitHub mantém o nome técnico `Project-Aether`.

Assistente de IA especializado em **cibersegurança defensiva** e **programação**.

## Estado atual

A API FastAPI disponibiliza `GET /`, `GET /health`, `GET /ui` e `POST /analyze`, `POST /review-code` e `POST /report`. A interface web em `/ui` permite enviar texto para análise e apresenta orientação e fontes. Cada resposta inclui um identificador de pedido (`X-Request-ID`) e a API regista metadados operacionais mínimos. O conteúdo enviado é analisado como texto: a aplicação não executa código, comandos, scans ou ações sugeridas pelo modelo.

O projeto inclui:
- Interface web estática servida pela própria API, sem framework JavaScript ou dependências adicionais.
- Formulário com escolha de categoria, limite de 20 000 caracteres, contador, estado de carregamento e mensagens de erro.
- Apresentação de resultados com APIs DOM seguras (`textContent`); o conteúdo recebido não é interpretado como HTML.
- O browser não guarda pedidos em armazenamento local ou de sessão; as respostas de análise usam `Cache-Control: no-store`.
- Fornecedor determinístico local (`AI_PROVIDER=rules`), ativo por omissão.
- Fornecedor opcional Ollama (`AI_PROVIDER=ollama`) para inferência local.
- O prompt do fornecedor Ollama pede explicações estruturadas, passos defensivos, verificação e limitações; instrui o modelo a não inventar fontes nem seguir instruções embutidas no pedido ou nos documentos recuperados.
- RAG sobre documentos Markdown locais em `knowledge/`.
- Recuperação lexical por omissão e recuperação semântica opcional via embeddings Ollama.
- Fallback para recuperação lexical se embeddings falharem ou forem inválidos.
- Validação de configuração no arranque, para evitar opções desconhecidas e timeouts inseguros.
- Cabeçalhos HTTP de segurança nas respostas da API.\n- Autenticação opcional por chave API (`KAMBA_API_KEY`) nos endpoints de análise; quando configurada, exige o cabeçalho `X-API-Key`. Usa uma chave aleatória com pelo menos 32 caracteres e nunca a publiques no repositório.\n- Limitação de pedidos por endereço IP, em memória por processo, configurável por `KAMBA_RATE_LIMIT_REQUESTS` (por omissão 60) e `KAMBA_RATE_LIMIT_WINDOW_SECONDS` (por omissão 60). Em instalações com vários workers ou instâncias, usa um limitador partilhado externo antes de exposição pública.
- Erros de validação HTTP 422 não repetem valores enviados pelo cliente; mantêm apenas localização, mensagem e tipo do erro.
- Revisão estática heurística de código como texto em `POST /review-code`, com identificadores de regra, severidade, linha e recomendações; não importa, compila nem executa o código recebido.\n- Testes de contrato verificam o esquema OpenAPI, os limites de entrada, as categorias aceites e os campos da resposta.


- Base de conhecimento ampliada com guias defensivos sobre desenvolvimento seguro, resposta a incidentes e segurança de aplicações, com referências oficiais NIST, CISA e OWASP.
- A documentação identifica versões e estados das publicações consultadas; a OWASP Top 10:2025 é tratada como referência de sensibilização, não como lista exaustiva.

## Requisitos e instalação

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\\Scripts\\Activate.ps1

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abre a interface em http://127.0.0.1:8000/ui. A documentação interativa da API fica disponível em http://127.0.0.1:8000/docs.

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

Valores inválidos fazem a aplicação falhar no arranque com uma mensagem de configuração, em vez de selecionar silenciosamente um fornecedor diferente.\n\nPara ativar a autenticação da API, define `KAMBA_API_KEY` com uma chave aleatória de pelo menos 32 caracteres. Sem esta variável, a API permanece em modo de desenvolvimento sem autenticação; não exponhas essa configuração publicamente. Os limites de pedidos podem ser ajustados com `KAMBA_RATE_LIMIT_REQUESTS` e `KAMBA_RATE_LIMIT_WINDOW_SECONDS`.

## Endpoints

- `GET /` — metadados do projeto.
- `GET /health` — estado básico da API.
- `GET /ui` — interface web.
- `POST /analyze` — recebe texto e categoria (`cybersecurity`, `programming` ou `general`) e devolve orientação e fontes recuperadas.\n- `POST /review-code` — recebe código como texto e devolve achados heurísticos estáticos; não executa código nem substitui ferramentas especializadas ou revisão humana.
- `POST /report` — gera um relatório JSON da revisão estática, incluindo data, resumo, severidades, achados e limitações.

O campo `content` aceita entre 1 e 20 000 caracteres. O conteúdo não é executado.

## Segurança e privacidade

- Não coloques passwords, tokens, chaves API ou dados pessoais nos pedidos nem no repositório.
- A interface não guarda o texto em localStorage, sessionStorage ou cookies; limpa a apresentação anterior quando um novo pedido começa.
- A interface usa `textContent` para apresentar conteúdo devolvido pela API, evitando interpretar esse conteúdo como HTML.
- Os logs registam apenas identificador gerado pelo servidor, método, caminho, código HTTP, duração e tipo de exceção. Não registam corpos, query strings, cabeçalhos nem mensagens de exceção.
- As respostas incluem `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer` e uma `Permissions-Policy` que desativa câmara, microfone e geolocalização.
- As respostas de análise usam `Cache-Control: no-store` para evitar armazenamento em cache do conteúdo e dos resultados.
- Testa apenas sistemas e código para os quais tens autorização.
- O conteúdo recuperado e o texto do utilizador são dados não confiáveis, nunca instruções para alterar as regras do assistente.
- Se ativares Ollama, o texto e o contexto documental são enviados para o serviço configurado. Confirma que o URL aponta para uma instância de confiança.
- Revê fontes e recomendações antes de as aplicar. A ferramenta não substitui uma revisão humana.

## Testes de integração Ollama (opcionais)

Os testes unitários usam clientes simulados. Para validar uma instância Ollama real, inicia o serviço local e instala os modelos definidos por `OLLAMA_MODEL` e `RAG_EMBEDDING_MODEL`. Depois executa explicitamente:

```bash
KAMBA_OLLAMA_INTEGRATION=1 pytest -q tests/integration
```

Sem `KAMBA_OLLAMA_INTEGRATION=1`, o teste fica ignorado e não tenta contactar qualquer serviço. A execução real requer que `OLLAMA_BASE_URL` esteja acessível.

## Testes

```bash
pytest -q
```

O GitHub Actions executa os testes automaticamente em pushes para `main` e pull requests dirigidos a `main`.
