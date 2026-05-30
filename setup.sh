#!/usr/bin/env bash
set -Eeuo pipefail

readonly GO_VERSION="go1.26.0"
readonly GO_ARCH="linux-amd64"
readonly GO_TAR="${GO_VERSION}.${GO_ARCH}.tar.gz"
readonly GO_URL="https://go.dev/dl/${GO_TAR}"

readonly GITSYNCURL="https://raw.githubusercontent.com/senapk/tko-student-starter/refs/heads/main/git-sync.sh"
readonly SETUPSHURL="https://raw.githubusercontent.com/senapk/tko-student-starter/refs/heads/main/setup.sh"

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

ensure_python() {
    # se estiver no windows, instalar via loja do windows
    if [[ "$OSTYPE" == "msys"* || "$OSTYPE" == "cygwin"* ]]; then
        if command_exists python; then
            return
        fi
        error "Python não encontrado. No windows, instale o Python pela loja do windows, depois 'python3 -m pip install --user pipx' e depois 'python3 -m pipx ensurepath'."
    fi
    
    # se estiver no linux, instalar via apt ou verificar se já está instalado
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists python3; then
            return
        fi
        if command_exists apt; then
            step "Instalando Python via apt"
            sudo apt update
            sudo apt install -y python3 python3-pip
            return
        fi
        error "Python não encontrado. Instale o Python 3 e pip usando o gerenciador de pacotes da sua distribuição (ex: apt para Debian/Ubuntu) ou baixe do site oficial."
    fi
    exit 1
}

ensure_pipx() {
    if command_exists pipx; then
        return
    fi

    error "pipx não encontrado. Instale o pipx e reinicie o terminal."
    error "No windows, instale o Python pela loja do windows, depois 'python3 -m pip install --user pipx' e depois 'python3 -m pipx ensurepath'."
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

ensure_basic() {
    if pipx list | grep -qE 'package tko '; then
        return
    fi

    setup_tko
    setup_basic
}

setup_tko() {
    step "Instalando/atualizando TKO"

    ensure_python
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
        editorconfig.editorconfig 

    success "Ambiente básico configurado"
}

setup_python() {
    ensure_basic
    ensure_python
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
    ensure_basic
    step "Configurando TypeScript"

    install_global_npm typescript esbuild
    npm install --save-dev @types/node readline-sync 2>/dev/null || true

    success "Ambiente TypeScript configurado"
}

setup_go() {
    ensure_basic
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

update_scripts() {
    step "Atualizando scripts"

    if ! command_exists curl; then
        error "curl não encontrado"
        exit 1
    fi

    printf "%b\n" "${GREEN}-> Atualizando git-sync.sh${RESET}"
    curl -fsSL "${GITSYNCURL}" -o git-sync.sh
    chmod +x git-sync.sh

    printf "%b\n" "${GREEN}-> Atualizando setup.sh${RESET}"
    curl -fsSL "${SETUPSHURL}" -o setup.sh
    chmod +x setup.sh

    success "Scripts atualizados"
}

setup_java() {
    ensure_basic
    step "Configuração Java"
    if ! command_exists apt; then
        error "apt não encontrado. Configuração Java só é suportada em sistemas baseados em Debian/Ubuntu (incluindo WSL)."
        return
    fi
    sudo apt update
    sudo apt install -y openjdk-17-jdk
    install_vscode_extensions vscjava.vscode-java-pack
    success "Ambiente Java configurado"
}


setup_c() {
    ensure_basic
    step "Configuração C/C++"
    if ! command_exists apt; then
        error "apt não encontrado. Configuração C/C++ só é suportada em sistemas baseados em Debian/Ubuntu (incluindo WSL)."
        return
    fi
    sudo apt update
    sudo apt install -y build-essential gdb
    install_vscode_extensions ms-vscode.cpptools
    success "Ambiente C/C++ configurado"
}

show_menu() {

    printf "\n========================================"
    printf "\n  Setup de Ambiente de Desenvolvimento"
    printf "\n========================================"
    printf "\n"
    printf "\nDigite o número do elemento que deseja instalar/atualizar:"
    printf "\n"
    printf "\n  1) ${GREEN}tko        ${RESET}Instala/atualiza o TKO (via pipx)"
    printf "\n  2) ${GREEN}scripts    ${RESET}Atualiza git-sync.sh e setup.sh scripts (via curl)"
    printf "\n  3) ${GREEN}python     ${RESET}Configura análise Python no workspace (via settings.json e extensão do VS Code)"
    printf "\n  4) ${GREEN}c          ${RESET}Configura ambiente C/C++(via apt/WSL)"
    printf "\n  5) ${GREEN}typescript ${RESET}Instala TypeScript, esbuild e dependências de apoio (via npm)"
    printf "\n  6) ${GREEN}go         ${RESET}Instala Go no sistema e extensão do VS Code (LINUX/WSL)"
    printf "\n  7) ${GREEN}java       ${RESET}Configura ambiente Java (via apt/WSL)"
    printf "\n"
}

main() {
    show_menu

    local choice
    read -rp "Escolha [1-7]: " choice

    case "$choice" in
        1)
            setup_tko
            ;;
        2)
            update_scripts
            ;;
        3)
            setup_python
            ;;
        4)
            setup_c
            ;;
        5)
            setup_typescript
            ;;
        6)
            setup_go
            ;;
        7)
            setup_java
            ;;
        *)
            error "Opção inválida"
            exit 1
            ;;
    esac

    printf "\n%b\n" "${GREEN}${BOLD}Setup concluído.${RESET}"
}

main "$@"
