#!/usr/bin/env bash
set -euo pipefail

GO_VERSION="go1.26.0"
GO_ARCH="linux-amd64"
GO_TAR="${GO_VERSION}.${GO_ARCH}.tar.gz"
GO_URL="https://go.dev/dl/${GO_TAR}"

log() { echo -e "\n==> $1"; }

command_exists() { command -v "$1" >/dev/null 2>&1; }

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
    command_exists code || return

    mapfile -t installed < <(code --list-extensions)

    for ext in "$@"; do
        printf '%s\n' "${installed[@]}" | grep -qx "$ext" \
            && echo "✓ $ext já instalada" \
            || { echo "→ Instalando $ext"; code --install-extension "$ext"; }
    done
}

install_global_npm() {
    command_exists npm || { echo "npm não encontrado"; return; }
    npm install -g "$@"
}

# ==============================
# tko
# ==============================

setup_tko() {
    log "Instalando/atualizando tko"

    command_exists pipx || { echo "pipx não encontrado"; exit 1; }

    if pipx list | grep -qE 'package tko '; then
        pipx upgrade tko
    else
        pipx install tko
    fi
}

# ==============================
# Básico
# ==============================

setup_basic() {
    log "Configurando ambiente básico"

    install_vscode_extensions \
        usernamehw.errorlens \
        bierner.markdown-preview-github-styles \
        tamasfe.even-better-toml
}

# ==============================
# Python
# ==============================

setup_python() {
    log "Configurando Python"

    write_if_missing ".vscode/settings.json" \
'{
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace"
}'

    install_vscode_extensions ms-python.python
}

# ==============================
# TypeScript
# ==============================

setup_typescript() {
    log "Configurando TypeScript"

    install_global_npm typescript esbuild
    npm install --save-dev @types/node readline-sync 2>/dev/null || true
}

# ==============================
# Go
# ==============================

setup_go() {
    log "Instalando Go ${GO_VERSION}"

    TMP="/tmp/${GO_TAR}"

    command_exists curl || { echo "curl não encontrado"; exit 1; }

    curl -fsSL "${GO_URL}" -o "${TMP}"

    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf "${TMP}"
    rm -f "${TMP}"

    ensure_path_export ~/.profile
    ensure_path_export ~/.bashrc

    install_vscode_extensions golang.Go
}

# ==============================
# Menu
# ==============================

echo "========================================"
echo "   Setup de Ambiente de Desenvolvimento"
echo "========================================"

echo "1) TKO (Instalar / Atualizar)"
echo "2) Python"
echo "3) TypeScript"
echo "4) Golang"

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
        echo "Opção inválida"
        exit 1
        ;;
esac

echo -e "\n✓ Setup concluído"