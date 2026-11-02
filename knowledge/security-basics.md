# Fundamentos de segurança defensiva

## Princípio do menor privilégio
Concede a cada utilizador, processo e serviço apenas as permissões estritamente necessárias. Revê permissões periodicamente, remove acessos obsoletos e utiliza contas distintas para tarefas administrativas.

Referência: NIST SP 800-53, control AC-6 — https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final

## Gestão de vulnerabilidades
Mantém inventário de ativos e dependências, acompanha avisos dos fabricantes, prioriza atualizações pelo risco e valida correções num ambiente controlado. Regista a versão afetada, a mitigação e a evidência da correção.

Referência: CISA Known Exploited Vulnerabilities Catalog — https://www.cisa.gov/known-exploited-vulnerabilities-catalog

## Desenvolvimento seguro
Valida entradas no servidor, codifica saídas conforme o contexto, protege segredos fora do código-fonte, atualiza dependências e adiciona testes para casos limite. Não confies em dados fornecidos pelo cliente.

Referência: OWASP Application Security Verification Standard — https://owasp.org/www-project-application-security-verification-standard/

## Resposta a incidentes
Prepara um plano de resposta, define responsáveis, preserva registos relevantes e segue um processo documentado de contenção, erradicação e recuperação. Analisa o incidente para reduzir a probabilidade de recorrência.

Referência: NIST SP 800-61 Rev. 2 — https://csrc.nist.gov/pubs/sp/800/61/r2/final
