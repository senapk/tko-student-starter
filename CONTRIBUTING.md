# Contribuindo com o TKO Student Starter

Este repositório serve como base para alunos, monitores e mantenedores do starter.

## Objetivo das contribuições

Contribuições devem priorizar:

- clareza para alunos iniciantes
- previsibilidade de uso em Ubuntu e Codespaces
- scripts simples, robustos e fáceis de manter
- documentação objetiva e operacional

## Antes de abrir uma mudança

1. Verifique se a alteração melhora o fluxo do aluno ou a manutenção do starter.
2. Evite adicionar complexidade desnecessária.
3. Preserve a compatibilidade com o fluxo atual em `main`.
4. Atualize a documentação quando a mudança afetar uso, setup ou sincronização.

## Padrões deste repositório

- Scripts shell devem continuar compatíveis com Bash.
- Mudanças em `setup.sh` e `git-sync.sh` devem manter mensagens claras para uso educacional.
- Arquivos de documentação devem permanecer em português.
- Mudanças de comportamento devem vir acompanhadas de atualização no `README.md`.

## Checklist de contribuição

1. Revise o impacto da mudança no fluxo do aluno.
2. Rode `bash -n setup.sh`.
3. Rode `bash -n git-sync.sh`.
4. Verifique `./setup.sh --help`.
5. Verifique `./git-sync.sh --help`.
6. Atualize documentação relacionada.

## Tipos de contribuição úteis

- melhoria de onboarding
- redução de erros comuns
- mensagens de erro mais claras
- validações preventivas
- compatibilidade com Codespaces
- melhorias de documentação e manutenção

## O que evitar

- dependências desnecessárias
- automações frágeis ou excessivamente acopladas
- alterações que escondam o funcionamento do Git do aluno
- mudanças que aumentem a dificuldade de suporte em sala
