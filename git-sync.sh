#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEFAULT_COMMIT_MESSAGE="sync update"
readonly ALLOWED_BRANCH="main"
readonly GIT="git"

readonly LOG_DIR=".git_logs"
readonly LOG_TIMESTAMP="$(date +"%Y-%m-%d_%H-%M-%S")"
readonly LOG_FILE="$LOG_DIR/$LOG_TIMESTAMP.log"

readonly RED='\033[31m'
readonly GREEN='\033[32m'
readonly YELLOW='\033[33m'
readonly BLUE='\033[34m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

print_help() {
  cat <<EOF
Uso: ./git-sync.sh [opcao]

Sincroniza o repositório do aluno com o remoto de forma guiada:
1) valida ambiente e branch
2) comita alterações locais (se houver)
3) atualiza com origin/main
4) envia commits para o remoto

Opcoes:
  -h, --help    Mostra esta ajuda e sai
EOF
}

parse_args() {
  case "${1:-}" in
    "" ) ;;
    -h|--help)
      print_help
      exit 0
      ;;
    *)
      printf "%b\n" "${RED}[ERRO]${RESET} Opção inválida: $1"
      print_help
      exit 1
      ;;
  esac
}

init_logging() {
  mkdir -p "$LOG_DIR"

  exec > >(
    tee >(
      sed -r 's/\x1B\[[0-9;]*[mK]//g' >> "$LOG_FILE"
    )
  ) 2>&1
}

trap 'printf "%b\n" "${RED}[ERRO]${RESET} Falha na linha $LINENO: $BASH_COMMAND"' ERR
trap 'echo; printf "%b\n" "${YELLOW}[AVISO]${RESET} Operação cancelada pelo usuário."' INT

step() { printf "\n%b\n" "${BLUE}${BOLD}==>${RESET} ${BOLD}$1${RESET}"; }
success() { printf "%b\n" "${GREEN}[OK]${RESET} $1"; }
warn() { printf "%b\n" "${YELLOW}[AVISO]${RESET} $1"; }
error() { printf "%b\n" "${RED}[ERRO]${RESET} $1"; }

run() {
  printf "%b\n" "${GREEN}-> $*${RESET}"
  "$@"
}

run_git_color() {
  local display="$1"
  shift
  printf "%b\n" "${GREEN}-> git $display${RESET}"
  git -c color.ui=always "$@"
}

ask() {
  local answer
  read -r -p "$1" answer
  echo "$answer"
}

confirm() {
  local answer
  read -r -p "$1 [Y/n] (Enter confirma): " answer
  case "${answer,,}" in
    ""|y|yes|s|sim) return 0 ;;
    *) return 1 ;;
  esac
}

is_merge_in_progress() {
  $GIT rev-parse -q --verify MERGE_HEAD >/dev/null 2>&1
}

has_merge_conflicts() {
  $GIT diff --name-only --diff-filter=U | grep -q .
}

has_local_changes() {
  ! $GIT diff --quiet || ! $GIT diff --cached --quiet
}

has_remote() {
  $GIT remote get-url origin >/dev/null 2>&1
}

has_upstream() {
  $GIT rev-parse --abbrev-ref --symbolic-full-name "@{u}" >/dev/null 2>&1
}

has_commits_to_push() {
  if ! has_upstream; then
    return 0
  fi

  [[ "$($GIT rev-list --count "@{u}..HEAD")" -gt 0 ]]
}

remote_has_updates() {
  local branch="$1"
  local ahead_behind
  ahead_behind="$(
    $GIT rev-list --left-right --count HEAD..."origin/$branch"
  )"

  local behind
  behind="$(echo "$ahead_behind" | awk '{print $2}')"

  [[ "$behind" -gt 0 ]]
}

validate_environment() {
  step "Validando ambiente"

  if ! $GIT rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    error "Esse diretório não é um repositório git."
    exit 1
  fi

  success "Repositório git detectado"
}

validate_remote() {
  step "Verificando conexão com o servidor"

  if ! has_remote; then
    error "Remote 'origin' não configurado."
    exit 1
  fi

  success "Conexão com servidor OK"
}

get_current_branch() {
  local branch
  branch="$($GIT rev-parse --abbrev-ref HEAD)"

  if [[ "$branch" == "HEAD" ]]; then
    error "Você está em HEAD destacado."
    exit 1
  fi

  if [[ "$branch" != "$ALLOWED_BRANCH" ]]; then
    error "Branch inválida: $branch"
    exit 1
  fi

  echo "$branch"
}

setup_git_identity() {
  step "Verificando identidade do git"

  local git_user_name
  local git_user_email

  git_user_name="$($GIT config --get user.name || true)"
  git_user_email="$($GIT config --get user.email || true)"

  if [[ -z "$git_user_name" ]]; then
    local name
    name="$(ask "Digite seu nome: ")"
    run $GIT config user.name "$name"
  fi

  if [[ -z "$git_user_email" ]]; then
    local email
    email="$(ask "Digite seu email: ")"
    run $GIT config user.email "$email"
  fi

  success "Identidade git configurada"
}

show_status() {
  step "Resumo do repositório (?? = novo, M = modificado, D = deletado, UU = conflito)"
  run_git_color "status --short" status --short || true
}

git_commit_changes() {
  local msg="$1"
  run $GIT commit -m "$msg"
}

commit_local_changes() {
  step "Verificando alterações locais"

  if ! has_local_changes; then
    success "Nenhuma alteração local encontrada"
    return
  fi

  if ! confirm "Deseja salvar essas alterações agora?"; then
    warn "Operação cancelada."
    exit 0
  fi

  run $GIT add -A

  if $GIT diff --cached --quiet; then
    warn "Nenhuma alteração pronta para commit."
    return
  fi

  warn "Resumo das alterações:"
  run_git_color "diff --cached --stat" diff --cached --stat

  local msg

  while true; do
    msg="$(ask "Mensagem do commit: ")"

    if [[ -z "${msg// }" ]]; then
      error "A mensagem de commit não pode ser vazia."
      continue
    fi

    break
  done

  git_commit_changes "$msg"

  success "Alterações salvas"
}

resolve_merge_conflict() {
  step "Conflitos detectados"

  local conflicts
  conflicts="$($GIT diff --name-only --diff-filter=U || true)"

  echo "$conflicts"

  while read -r file; do
    [[ -z "$file" ]] && continue

    echo "Arquivo em conflito: $file"

    echo "1) Manter MINHA versão"
    echo "2) Manter versão do SERVIDOR"
    echo "3) Resolver manualmente"

    local choice
    choice="$(ask "> ")"

    case "$choice" in
      1)
        run $GIT checkout --ours -- "$file"
        run $GIT add "$file"
        ;;
      2)
        run $GIT checkout --theirs -- "$file"
        run $GIT add "$file"
        ;;
      *)
        warn "Resolva manualmente e execute novamente."
        exit 0
        ;;
    esac
  done <<< "$conflicts"

  if ! $GIT diff --cached --quiet; then
    run $GIT commit -m "resolve merge conflicts"
  fi

  success "Conflitos resolvidos"
}

handle_pending_merge() {
  if ! is_merge_in_progress; then
    return
  fi

  step "Merge pendente detectado"

  if has_merge_conflicts; then
    resolve_merge_conflict
    return
  fi

  run $GIT add -A

  if ! $GIT diff --cached --quiet; then
    run $GIT commit --no-edit
  fi
}

sync_with_remote() {
  local branch="$1"

  step "Baixando atualizações do servidor"

  run $GIT fetch origin

  if ! remote_has_updates "$branch"; then
    success "Seu repositório já está atualizado"
    return
  fi

  if ! confirm "Deseja continuar?"; then
    warn "Operação cancelada."
    exit 0
  fi

  set +e

  run $GIT merge --ff-only "origin/$branch"
  local merge_status=$?

  if [[ $merge_status -ne 0 ]]; then
    warn "Fast-forward não foi possível. Tentando merge."

    run $GIT merge "origin/$branch"
    merge_status=$?
  fi

  set -e

  if [[ $merge_status -ne 0 ]]; then
    if is_merge_in_progress; then
      resolve_merge_conflict
      return
    fi

    error "Erro ao atualizar repositório"
    exit "$merge_status"
  fi

  success "Atualizações recebidas"
}

push_changes() {
  local branch="$1"

  step "Enviando alterações para o servidor"

  if ! has_commits_to_push; then
    success "Nenhum commit novo para enviar"
    return
  fi

  if has_upstream; then
    run $GIT push
  else
    run $GIT push -u origin "$branch"
  fi

  success "Alterações enviadas"
}

show_final_summary() {
  step "Resumo final"

  printf "%b\n" "${GREEN}✓${RESET} alterações salvas"
  printf "%b\n" "${GREEN}✓${RESET} repositório atualizado"
  printf "%b\n" "${GREEN}✓${RESET} alterações enviadas"

  step "Log salvo em: $LOG_FILE"
}

main() {
  parse_args "${1:-}"
  init_logging

  printf "%b\n" "${BOLD}SYNC EDUCACIONAL GIT${RESET}"

  validate_environment
  validate_remote
  setup_git_identity

  local branch
  branch="$(get_current_branch)"

  show_status

  handle_pending_merge
  commit_local_changes
  sync_with_remote "$branch"
  push_changes "$branch"

  show_final_summary

  printf "%b\n" "${GREEN}${BOLD}Sync concluído com sucesso.${RESET}"
}

main "$@"
