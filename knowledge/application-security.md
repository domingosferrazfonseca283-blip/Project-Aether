# Segurança de aplicações

## Categorias de risco OWASP
O OWASP Top 10 é um documento de sensibilização sobre riscos comuns em aplicações web, não uma lista exaustiva nem uma certificação. A versão publicada mais recente identificada é a OWASP Top 10:2025. Usa as categorias para orientar revisão e formação, mas avalia sempre a arquitetura e o contexto concretos.

Áreas de atenção incluem controlo de acesso, configuração segura, cadeia de fornecimento de software, falhas criptográficas, injeção, desenho inseguro, autenticação, integridade de software e dados, registo e monitorização e tratamento de condições excepcionais.

Referência oficial:
- OWASP Top 10 — versão 2025: https://owasp.org/projects/top-ten/

## Controlo de acesso e autenticação
Aplica negação por omissão e verifica autorização no servidor em cada pedido e recurso. Não confies em identificadores ou permissões fornecidos pelo browser. Usa autenticação multifator quando disponível, armazena palavras-passe com algoritmos de hash próprios para credenciais e protege os processos de recuperação de conta. Limita tentativas e regista eventos relevantes sem guardar segredos.

## Validação, codificação e configuração
Valida tipo, formato, tamanho e intervalo dos dados no servidor. Usa consultas parametrizadas para acesso a bases de dados e codifica saídas conforme o contexto para reduzir riscos de injeção e interpretação indevida. Desativa funcionalidades e serviços desnecessários, restringe origens e permissões, protege cabeçalhos e evita expor mensagens internas.

## Dependências, registos e testes
Mantém dependências atualizadas e inventariadas, acompanha avisos dos fornecedores e revê alterações antes da publicação. Os registos devem permitir investigação sem incluir passwords, tokens ou conteúdo pessoal desnecessário. Testa autorização, validação, sessões, limites de utilização, erros e recuperação. Realiza testes apenas em aplicações e ambientes para os quais existe autorização explícita.
