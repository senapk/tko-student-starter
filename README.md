---
nomeAluno: "Seu nome"
matricula: "Digite sua matrícula aqui por obséquio"
---

# TKO Student Starter

Repositório base do aluno para uso com o TKO: https://github.com/senapk/tko.

Este projeto foi preparado para uso em ambiente Git e possui dois scripts principais:

- `setup.sh`: prepara o ambiente de desenvolvimento no Ubuntu ou Codespaces, com execução manual pelo aluno.
- `git-sync.sh`: padroniza o fluxo de sincronização do repositório do aluno (commit, pull/merge e push).

## O que este starter resolve

- Setup inicial do ambiente para uso com TKO.
- Padronização de fluxo Git para alunos.
- Uso orientado em Ubuntu e GitHub Codespaces, com setup manual e previsível.
- Redução de erros comuns de configuração e sincronização.
- Base pronta para ser expandida com linguagens e exercícios do curso.

## Início rápido

Se você quer começar em poucos minutos:

1. Abra o projeto no Codespaces ou em um Ubuntu local.
2. Execute `./setup.sh` e escolha a opção desejada.
3. Faça suas atividades normalmente.
4. Execute `./git-sync.sh` para sincronizar suas alterações.

## Objetivo deste repositório

- Servir como ponto de partida para atividades e avaliações com TKO.
- Reduzir problemas de configuração inicial do ambiente.
- Oferecer um fluxo Git guiado para estudantes.

## Estrutura profissional adicionada

- `.gitattributes`: força tratamento consistente de arquivos texto no Git.
- `.gitignore`: evita commit de logs, artefatos temporários e diretórios locais.
- `CONTRIBUTING.md`: orienta contribuições de monitores e mantenedores.

## Manutenção do starter

- Para contribuir com melhorias no repositório, consulte `CONTRIBUTING.md`.
- Para reportar bugs ou propor melhorias, use os templates em `.github/ISSUE_TEMPLATE/`.

## Scripts principais

### `setup.sh` (Ubuntu/Codespaces)

Script interativo para configurar o ambiente. Ao executar, você escolhe uma opção de setup:

- `1) TKO`: instala ou atualiza o TKO via `pipx` e configura extensões básicas do VS Code.
- `2) Python`: aplica configurações de análise Python no workspace e instala extensão Python.
- `3) TypeScript`: instala ferramentas globais (`typescript`, `esbuild`) e dependências de apoio.
- `4) Golang`: instala Go no sistema, ajusta `PATH` e instala extensão Go.

Uso:

```bash
./setup.sh
```

Ajuda:

```bash
./setup.sh --help
```

Quando usar:

- Primeira configuração da máquina/ambiente.
- Atualização das ferramentas do curso.
- Mudança de linguagem principal do semestre (Python, TypeScript ou Go).

### `git-sync.sh` (sincronização Git do aluno)

Script de sincronização com foco educacional para manter o repositório organizado e atualizado.

Principais responsabilidades:

- Valida se você está em um repositório Git válido e na branch permitida (`main`).
- Verifica e configura identidade Git (`user.name` e `user.email`) quando necessário.
- Detecta alterações locais e oferece commit guiado com mensagem obrigatória.
- Busca atualizações do remoto (`origin`) e tenta aplicar `fast-forward` primeiro.
- Se necessário, realiza merge e auxilia na resolução de conflitos.
- Envia commits locais para o repositório remoto.
- Gera log de execução em `.git_logs/`.

Uso:

```bash
./git-sync.sh
```

Quando usar:

- Ao terminar uma atividade ou etapa de implementação.
- Antes de encerrar uma sessão de trabalho.
- Sempre que quiser reduzir risco de divergência com o remoto.

## Setup local (máquina própria)

Pré-requisitos mínimos:

- `git`
- `python` (com `pip`)
- `pipx`
- VS Code
- Acesso ao GitHub com chave SSH configurada

- Para a primeira configuração:
  - Instale `git`, `python`, compiladores e VS Code.
  - Configure sua chave SSH para uso com GitHub.
  - Configure `pipx`:
    - `pipx ensurepath`
    - reinicie o terminal.
  - Instale o TKO:
    - `pipx install tko`

## Setup no Codespaces

No Codespaces, o fluxo recomendado continua sendo manual, com o aluno executando o setup explicitamente.

Fluxo recomendado:

```bash
./setup.sh
```

Isso evita inicializações automáticas inesperadas e mantém o comportamento alinhado ao fluxo adotado também fora do Codespaces.

## Fluxo recomendado de trabalho

1. Faça setup do ambiente com `./setup.sh`.
2. Desenvolva suas atividades normalmente.
3. Sincronize com o remoto usando `./git-sync.sh` ao finalizar uma etapa.

## Fluxo do aluno

1. Abra o repositório.
2. Configure o ambiente com `./setup.sh`.
3. Resolva a atividade no diretório do projeto.
4. Revise suas alterações.
5. Execute `./git-sync.sh`.
6. Confirme no GitHub se o envio foi concluído.

## Checklist antes de sincronizar

1. Rode e valide seus testes locais (quando existirem).
2. Revise os arquivos alterados e remova artefatos temporários.
3. Confirme se está na branch `main`.
4. Execute `./git-sync.sh`.
5. Verifique no GitHub se o commit foi enviado corretamente.

## Observações

- Mantenha os campos do frontmatter no topo deste arquivo atualizados (`nomeAluno` e `matricula`).
- Execute os scripts com permissão de execução (`chmod +x setup.sh git-sync.sh`) caso necessário.
- Em caso de conflitos Git, o `git-sync.sh` oferece caminhos guiados de resolução.

## Dúvidas frequentes

- Preciso usar Codespaces?
  - Não. O repositório funciona em Ubuntu local, desde que as dependências mínimas estejam instaladas.
- O setup é automático ao abrir o repositório?
  - Não. O fluxo oficial é manual, inclusive no Codespaces, para evitar comportamentos inesperados entre sistemas diferentes.
- O `setup.sh` instala tudo de uma vez?
  - Não. Ele é interativo e permite escolher o tipo de configuração desejada.
- O `git-sync.sh` substitui o Git?
  - Não. Ele apenas organiza e simplifica o fluxo mais comum de sincronização.
- Posso trabalhar fora da branch `main`?
  - O fluxo atual do script foi deliberadamente restringido à branch `main`.

## Solução de problemas comuns

- Erro de permissão ao executar script:
  - Rode `chmod +x setup.sh git-sync.sh` e tente novamente.
- `pipx` não encontrado:
  - Instale o `pipx`, execute `pipx ensurepath` e reinicie o terminal.
- `git-sync.sh` recusando branch:
  - O fluxo é intencionalmente restrito à branch `main`.
- Falha de autenticação com GitHub:
  - Revise chave SSH, `origin` do repositório e permissões de acesso.
