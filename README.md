# Project Aether

Assistente de IA especializado em **cibersegurança defensiva** e **programação**.

## Objetivos
- Explicar conceitos de segurança, vulnerabilidades e CVEs.
- Ajudar a rever código e identificar práticas inseguras.
- Apoiar debugging e desenvolvimento em Python.
- Consultar documentação própria através de RAG numa fase posterior.

## Estado
A API suporta um fornecedor determinístico local (`rules`) e um adaptador opcional para Ollama (`ollama`). O modelo Ollama corre localmente; o projeto não inclui pesos nem treina modelos.

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

A API usa uma interface `AIProvider` em `app/ai/provider.py`. O fornecedor padrão é `RuleBasedProvider`, determinístico e sem rede. Opcionalmente, `OllamaProvider` comunica com um modelo executado no serviço Ollama local.

A seleção é feita através de `AI_PROVIDER`. A integração local não requer chaves API.


## Modelo local opcional (Ollama)

O fornecedor padrão é `rules`, que funciona sem rede. Para usar um modelo local:

1. Instala e inicia o Ollama no teu computador.
2. Obtém um modelo compatível através do próprio Ollama, por exemplo `qwen2.5:3b`.
3. Define as variáveis de ambiente antes de iniciar a API:

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

O adaptador usa a API local `/api/chat`, com timeout configurável por `OLLAMA_TIMEOUT_SECONDS`. Se o serviço local estiver indisponível, a API devolve HTTP 503. O texto submetido é enviado ao serviço Ollama indicado; não incluas passwords, tokens ou dados pessoais. A Aether não executa código, comandos ou ações sugeridas pelo modelo.



## Recuperação documental (RAG inicial)

A versão 0.4.0 inclui recuperação lexical local de secções Markdown em `knowledge/`. A API devolve as fontes encontradas em `sources`, incluindo caminho, secção, excerto e indicação de referência. O contexto recuperado é tratado como dado não confiável: não pode alterar as instruções do assistente nem desencadear execução de código.

A recuperação é deliberadamente simples (correspondência de termos), não utiliza embeddings nem pesquisa na Internet. As referências externas são apresentadas nos próprios documentos para consulta e validação. Adiciona apenas documentação técnica de fontes reconhecidas e revê-a antes de a integrar.
