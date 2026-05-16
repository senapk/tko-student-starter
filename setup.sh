#!/usr/bin/env bash
set -Eeuo pipefail

readonly GO_VERSION="go1.26.0"
readonly GO_ARCH="linux-amd64"
readonly GO_TAR="${GO_VERSION}.${GO_ARCH}.tar.gz"
readonly GO_URL="https://go.dev/dl/${GO_TAR}"

readonly RED='\033[31m'
readonly GREEN='\033[32m'
readonly YELLOW='\033[33m'
readonly BLUE='\033[34m'
readonly BOLD='\033[1m'
readonly RESET='\033[0m'

trap 'printf "%b\n" "${RED}[ERRO]${RESET} Falha na linha $LINENO: $BASH_COMMAND"' ERR

step() { printf "\n%b\n" "${BLUE}${BOLD}==>${RESET} ${BOLD}$1${RESET}"; }
success() { printf "%b\n" "${GREEN}[OK]${RESET} $1"; }
warn() { printf "%b\n" "${YELLOW}[AVISO]${RESET} $1"; }
error() { printf "%b\n" "${RED}[ERRO]${RESET} $1"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

print_help() {
    cat <<EOF
Uso: ./setup.sh [opcao]

Script de configuração do ambiente do aluno para uso com o TKO.

Opcoes:
  -h, --help    Mostra esta ajuda e sai

Menu interativo:
  1) TKO        Instala/atualiza o TKO e extensões básicas do VS Code
  2) Python     Configura análise Python no workspace
  3) TypeScript Instala TypeScript, esbuild e dependências de apoio
  4) Golang     Instala Go no sistema e extensão do VS Code
EOF
}

parse_args() {
    case "${1:-}" in
        "") ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            error "Opção inválida: $1"
            print_help
            exit 1
            ;;
    esac
}

validate_platform() {
    step "Validando plataforma"

    if [[ "$(uname -s)" != "Linux" ]]; then
        error "Este script foi preparado para ambientes Linux/Ubuntu/Codespaces."
        exit 1
    fi

    if [[ -f /etc/os-release ]]; then
        if ! grep -qiE 'ubuntu|debian' /etc/os-release; then
            warn "Ambiente não identificado como Ubuntu/Debian. O script pode funcionar parcialmente."
        fi
    fi

    success "Plataforma compatível detectada"
}

ensure_path_export() {
    local line='export PATH=$PATH:/usr/local/go/bin'
    local file="$1"
    [[ -f "$file" ]] || touch "$file"
    grep -qxF "$line" "$file" || echo "$line" >> "$file"
}

write_if_missing() {
    local file="$1"
    local content="$2"

    [[ -f "$file" ]] && return
    mkdir -p "$(dirname "$file")"
    printf "%s\n" "$content" > "$file"
}

install_vscode_extensions() {
    if ! command_exists code; then
        warn "CLI do VS Code não encontrada; extensões não serão instaladas automaticamente."
        return
    fi

    mapfile -t installed < <(code --list-extensions)

    for ext in "$@"; do
        if printf '%s\n' "${installed[@]}" | grep -qx "$ext"; then
            success "$ext já instalada"
            continue
        fi

        printf "%b\n" "${GREEN}-> code --install-extension $ext${RESET}"
        code --install-extension "$ext"
    done
}

install_global_npm() {
    if ! command_exists npm; then
        error "npm não encontrado"
        exit 1
    fi

    printf "%b\n" "${GREEN}-> npm install -g $*${RESET}"
    npm install -g "$@"
}

ensure_pipx() {
    if command_exists pipx; then
        return
    fi

    error "pipx não encontrado. Instale o pipx, execute 'pipx ensurepath' e reinicie o terminal."
    exit 1
}

ensure_sudo_for_go() {
    if [[ -w /usr/local ]]; then
        return
    fi

    if ! command_exists sudo; then
        error "sudo não encontrado. A instalação do Go requer acesso para gravar em /usr/local."
        exit 1
    fi
}

setup_tko() {
    step "Instalando/atualizando TKO"

    ensure_pipx

    if pipx list | grep -qE 'package tko '; then
        pipx upgrade tko
    else
        pipx install tko
    fi

    success "TKO pronto para uso"
}

setup_basic() {
    step "Configurando ambiente básico"

    install_vscode_extensions \
        usernamehw.errorlens \
        bierner.markdown-preview-github-styles \
        tamasfe.even-better-toml \
        editorconfig.editorconfig \
        github.vscode-github-actions

    success "Ambiente básico configurado"
}

setup_python() {
    step "Configurando Python"

    write_if_missing ".vscode/settings.json" \
'{
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace"
}'

    install_vscode_extensions ms-python.python

    success "Ambiente Python configurado"
}

setup_typescript() {
    step "Configurando TypeScript"

    install_global_npm typescript esbuild
    npm install --save-dev @types/node readline-sync 2>/dev/null || true

    success "Ambiente TypeScript configurado"
}

setup_go() {
    step "Instalando Go ${GO_VERSION}"

    local tmp="/tmp/${GO_TAR}"

    if ! command_exists curl; then
        error "curl não encontrado"
        exit 1
    fi

    ensure_sudo_for_go

    printf "%b\n" "${GREEN}-> curl -fsSL ${GO_URL} -o ${tmp}${RESET}"
    curl -fsSL "${GO_URL}" -o "${tmp}"

    printf "%b\n" "${GREEN}-> remover versão anterior do Go${RESET}"
    sudo rm -rf /usr/local/go
    printf "%b\n" "${GREEN}-> instalar ${GO_TAR} em /usr/local${RESET}"
    sudo tar -C /usr/local -xzf "${tmp}"
    rm -f "${tmp}"

    ensure_path_export ~/.profile
    ensure_path_export ~/.bashrc

    install_vscode_extensions golang.Go

    success "Ambiente Go configurado"
}

show_menu() {
    echo "========================================"
    echo "   Setup de Ambiente de Desenvolvimento"
    echo "========================================"
    echo
    echo "1) TKO (Instalar / Atualizar)"
    echo "2) Python"
    echo "3) TypeScript"
    echo "4) Golang"
}

main() {
    parse_args "${1:-}"
    validate_platform

    show_menu

    local choice
    read -rp "Escolha [1-4]: " choice

    case "$choice" in
        1)
            setup_tko
            setup_basic
            ;;
        2)
            setup_python
            ;;
        3)
            setup_typescript
            ;;
        4)
            setup_go
            ;;
        *)
            error "Opção inválida"
            exit 1
            ;;
    esac

    printf "\n%b\n" "${GREEN}${BOLD}Setup concluído.${RESET}"
}

main "$@"