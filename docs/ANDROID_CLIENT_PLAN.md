# Preparação do cliente Android da Kamba

## Objetivo e limite desta fase

A aplicação Android será um cliente da API Kamba. A lógica de análise, os fornecedores de IA, a recuperação documental e a base de conhecimento permanecem no backend. O cliente não incorpora modelos, chaves de fornecedor nem lógica de segurança que deva ser autoritativa.

Esta documentação prepara a integração; não significa que exista uma aplicação Android compilada ou pronta para instalar.

## Arquitetura prevista

```text
Aplicação Android
  └── HTTPS / JSON
       └── API FastAPI Kamba
            ├── autenticação e rate limiting
            ├── /analyze
            ├── /review-code
            ├── /report
            ├── provider rules ou Ollama
            └── RAG lexical ou embeddings Ollama
```

O backend é a fonte de verdade. O cliente apresenta resultados e erros, mas não executa código submetido nem interpreta respostas da API como HTML.

## Contrato HTTP

Todos os pedidos POST usam `Content-Type: application/json` e devem aceitar respostas JSON.

### Estado

- `GET /health` — estado básico do processo. Não confirma que Ollama, embeddings ou todos os serviços dependentes estão prontos.
- `GET /` — metadados e versão da API.

### Análise

`POST /analyze`

Pedido:

```json
{
  "content": "Como aplicar o princípio do menor privilégio?",
  "category": "cybersecurity"
}
```

Categorias aceites: `cybersecurity`, `programming`, `general`. O campo `content` deve conter entre 1 e 20 000 caracteres e não pode ser apenas espaços.

Resposta de sucesso (campos):

- `category`, `status`, `provider`
- `guidance`: lista de textos
- `sources`: lista de objetos com `source_id`, `title`, `path`, `excerpt` e `reference`

### Revisão estática

`POST /review-code`

Pedido: `{"content":"texto de código para revisão"}`

A resposta contém `status`, `analysis_mode` e `findings`. A análise é heurística e trata o código como texto; não o executa, importa nem compila.

### Relatório

`POST /report`

Pedido: `{"content":"texto de código para revisão"}`

Devolve um relatório JSON com nome, data, modo de análise, resumo, limitações e achados.

## Autenticação e transporte

- Em produção, usar exclusivamente HTTPS com certificado válido. Não desativar validação TLS.
- Se `KAMBA_API_KEY` estiver configurada no servidor, enviar `X-API-Key` em cada POST protegido (`/analyze`, `/review-code`, `/report`).
- Nunca incluir uma chave de servidor fixa dentro do APK ou no repositório. Uma chave partilhada embutida numa aplicação pode ser extraída.
- Para um serviço público, preferir autenticação por utilizador/dispositivo com credenciais de curta duração e revogáveis antes de distribuir a aplicação. A chave API atual é um controlo simples, não um sistema completo de identidade.
- Não guardar pedidos ou respostas confidenciais em logs, analytics, notificações ou backups.
- O servidor devolve `X-Request-ID`; o cliente pode apresentá-lo ao suporte, mas não deve permitir que o utilizador o defina como identificador de confiança.

## Tratamento de respostas e falhas

- `200`: validar os campos antes de apresentar o resultado.
- `401`: autenticação em falta ou inválida.
- `422`: pedido inválido; apresentar uma mensagem clara sem repetir dados confidenciais.
- `429`: limite de pedidos atingido; respeitar `Retry-After` quando presente.
- `503`: fornecedor de IA indisponível; permitir nova tentativa manual.
- Erro de rede ou timeout: indicar que não foi possível contactar o servidor; não fingir que a análise foi concluída.
- Respostas inesperadas ou JSON inválido: tratar como erro controlado, sem falhar a aplicação.

A interface deve impedir envios duplicados enquanto um pedido está em curso, permitir cancelar a espera no cliente quando possível e limpar resultados antigos quando começa uma nova análise.

## Endereços de desenvolvimento

- Emulador Android: para alcançar um backend no computador anfitrião, o endereço especial do emulador Android é normalmente `10.0.2.2`, não `127.0.0.1`.
- Telemóvel físico: usar o endereço LAN do computador/servidor, com ambos na mesma rede e firewall configurada de forma restrita.
- Backend no próprio telemóvel: `127.0.0.1` só é adequado se o servidor estiver a correr no mesmo dispositivo e a escutar na interface correta.
- Estes endereços são apenas para desenvolvimento. Não expor a API à Internet sem HTTPS, autenticação adequada, rate limiting partilhado e revisão de implantação.

## Critérios antes de iniciar a implementação Android

- [ ] CI verde no commit atual.
- [ ] Instalação e arranque do backend reproduzíveis num ambiente suportado.
- [ ] Testes de integração reais para Ollama, quando esse provider for usado.
- [ ] Decisão sobre alojamento, HTTPS, domínio e autenticação de utilizadores.
- [ ] Contratos de resposta estabilizados e documentados.
- [ ] Testes de API para 401, 422, 429, 503, timeout e respostas malformadas.
- [ ] Política de privacidade e retenção de dados definida.
- [ ] Escolha da tecnologia Android e testes em emulador e dispositivo físico.

## Decisão de produto ainda em aberto

A tecnologia da aplicação (Android nativo/Kotlin ou framework multiplataforma), o método de autenticação final e o alojamento de produção devem ser decididos antes de criar o projeto Android. Esta fase mantém a API independente da tecnologia escolhida.
