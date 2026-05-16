# Release Checklist

Checklist para manutenção e publicação de novas versões do starter.

## Antes da release

1. Revisar mudanças pendentes no `README.md`, `setup.sh` e `git-sync.sh`.
2. Confirmar que o fluxo principal continua na branch `main`.
3. Verificar se a documentação ainda corresponde ao comportamento real dos scripts.
4. Revisar arquivos de suporte do starter (`.editorconfig`, `.gitignore`, workflow, extensões recomendadas).

## Validação obrigatória

1. Rodar `bash -n setup.sh`.
2. Rodar `bash -n git-sync.sh`.
3. Rodar `./setup.sh --help`.
4. Rodar `./git-sync.sh --help`.
5. Verificar se `setup.sh` e `git-sync.sh` continuam executáveis.
6. Confirmar que o workflow de validação continua compatível.

## Validação funcional recomendada

1. Testar o fluxo de setup em Codespaces ou Ubuntu limpo.
2. Testar sincronização com alterações locais e remoto atualizado.
3. Simular cenário com conflito para revisar mensagens orientativas.
4. Confirmar instalação de extensões recomendadas.

## Antes de publicar

1. Atualizar documentação de onboarding se necessário.
2. Conferir se novos arquivos temporários não estão sendo versionados.
3. Revisar título e descrição da release ou changelog adotado pelo projeto.
4. Garantir que exemplos de comandos no README continuam válidos.

## Após publicar

1. Validar abertura do repositório em Codespaces.
2. Confirmar que o README continua claro para novos alunos.
3. Registrar ajustes pendentes identificados durante a publicação.
