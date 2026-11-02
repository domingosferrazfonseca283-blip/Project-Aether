# Desenvolvimento seguro de software

## Ciclo de desenvolvimento seguro
Integra segurança desde a definição de requisitos até à manutenção. Define requisitos de segurança e privacidade, identifica ativos e ameaças, revê decisões arquiteturais, aplica controlos no código, testa e acompanha vulnerabilidades após a publicação. Mantém evidências e responsáveis para cada risco relevante.

O NIST Secure Software Development Framework (SSDF) organiza práticas em quatro grupos: preparar a organização, proteger o software, produzir software seguro e responder a vulnerabilidades. A versão final publicada é a 1.1; a revisão 1.2 constava como projeto (draft) na página de publicações consultada em novembro de 2026.

Referências:
- NIST SP 800-218, SSDF 1.1 (final, fevereiro de 2022): https://csrc.nist.gov/pubs/sp/800/218/final
- NIST SSDF — publicações e estado das revisões: https://csrc.nist.gov/projects/ssdf/publications

## Proteção do código e da cadeia de fornecimento
Restringe permissões de repositórios, exige revisão de alterações, protege branches importantes e guarda segredos em mecanismos próprios de gestão de segredos. Mantém inventário de dependências, fixa versões quando adequado, acompanha avisos de segurança e remove componentes sem manutenção. Verifica a origem e integridade dos artefactos de build e limita quem pode publicar versões.

## Verificação e manutenção
Combina revisão manual, testes automatizados, análise estática e verificação de dependências. Trata os resultados como sinais para triagem: confirma contexto, versão afetada, exposição e impacto antes de priorizar. Corrige primeiro os riscos mais relevantes, testa a correção e regista a decisão. Não uses resultados de ferramentas como prova isolada de ausência de vulnerabilidades.

## Requisitos de aplicação
Valida entradas no servidor, aplica autorização em cada operação, codifica saídas conforme o contexto, usa mecanismos criptográficos reconhecidos e evita implementar algoritmos próprios. Protege sessões e dados sensíveis, configura mensagens de erro sem detalhes internos e testa controlos de acesso, limites e caminhos de falha.
