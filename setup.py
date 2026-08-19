#!/usr/bin/env python3

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.request import urlopen


# ============================================================
# Configuração
# ============================================================

GO_VERSION = "go1.26.0"
GO_ARCH = "linux-amd64"
GO_TAR = f"{GO_VERSION}.{GO_ARCH}.tar.gz"
GO_URL = f"https://go.dev/dl/{GO_TAR}"

GITSYNC_URL = (
    "https://raw.githubusercontent.com/senapk/tko-student-starter/"
    "refs/heads/main/git-sync.py"
)

SETUP_URL = (
    "https://raw.githubusercontent.com/senapk/tko-student-starter/"
    "refs/heads/main/setup.py"
)


RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ============================================================
# Interface
# ============================================================

def step(message: str) -> None:
    print(
        f"\n{BLUE}{BOLD}==>{RESET} "
        f"{BOLD}{message}{RESET}"
    )


def success(message: str) -> None:
    print(f"{GREEN}[OK]{RESET} {message}")


def warn(message: str) -> None:
    print(f"{YELLOW}[AVISO]{RESET} {message}")


def error(message: str) -> None:
    print(f"{RED}[ERRO]{RESET} {message}")


def show_menu() -> None:
    print(
        f"""
========================================
  Setup de Ambiente de Desenvolvimento
========================================

Digite o número do elemento que deseja instalar/atualizar:

  1) {GREEN}tko        {RESET}Instala/atualiza o TKO (via pipx)
  2) {GREEN}scripts    {RESET}Atualiza git-sync.py e setup.py 
  3) {GREEN}python     {RESET}Configura análise Python no workspace
  4) {GREEN}c          {RESET}Configura ambiente C/C++ (via apt/WSL)
  5) {GREEN}typescript {RESET}Instala TypeScript, esbuild e dependências (via npm)
  6) {GREEN}go         {RESET}Instala Go no sistema (LINUX/WSL)
  7) {GREEN}java       {RESET}Configura ambiente Java (via apt/WSL)
"""
    )


# ============================================================
# Sistema / comandos
# ============================================================

def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run(
    command: list[str],
    *,
    check: bool = True,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def download(url: str, destination: str | Path) -> None:
    path = Path(destination)

    with urlopen(url) as response:
        path.write_bytes(response.read())


def write_if_missing(
    file: str | Path,
    content: str,
) -> None:
    path = Path(file)

    if path.exists():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + "\n")


def ensure_path_export(file: str | Path) -> None:
    path = Path(file)
    line = "export PATH=$PATH:/usr/local/go/bin"

    path.touch(exist_ok=True)

    lines = path.read_text().splitlines()

    if line not in lines:
        with path.open("a") as stream:
            stream.write(line + "\n")


def is_writable(path: str | Path) -> bool:
    return os.access(path, os.W_OK)


# ============================================================
# Ferramentas
# ============================================================

def install_vscode_extensions(
    extensions: list[str],
) -> None:
    if not command_exists("code"):
        warn(
            "CLI do VS Code não encontrada; "
            "extensões não serão instaladas automaticamente."
        )
        return

    result = run(
        ["code", "--list-extensions"],
        capture_output=True,
    )

    installed = set(result.stdout.splitlines())

    for extension in extensions:
        if extension in installed:
            success(f"{extension} já instalada")
            continue

        print(
            f"{GREEN}-> code --install-extension "
            f"{extension}{RESET}"
        )

        run(
            [
                "code",
                "--install-extension",
                extension,
            ]
        )


def install_global_npm(
    packages: list[str],
) -> None:
    if not command_exists("npm"):
        error("npm não encontrado")
        raise SystemExit(1)

    print(
        f"{GREEN}-> npm install -g "
        f"{' '.join(packages)}{RESET}"
    )

    run(
        [
            "npm",
            "install",
            "-g",
            *packages,
        ]
    )


# ============================================================
# Python / pipx / TKO
# ============================================================

def ensure_python() -> None:
    system = platform.system()

    if system == "Windows":
        if command_exists("python"):
            return

        error(
            "Python não encontrado. No Windows, instale o Python "
            "pela loja do Windows, depois execute "
            "'python3 -m pip install --user pipx' e "
            "'python3 -m pipx ensurepath'."
        )

        raise SystemExit(1)

    if system == "Linux":
        if command_exists("python3"):
            return

        if command_exists("apt"):
            step("Instalando Python via apt")

            run(["sudo", "apt", "update"])

            run(
                [
                    "sudo",
                    "apt",
                    "install",
                    "-y",
                    "python3",
                    "python3-pip",
                ]
            )

            return

        error(
            "Python não encontrado. Instale o Python 3 e pip "
            "usando o gerenciador de pacotes da sua distribuição."
        )

        raise SystemExit(1)

    error("Sistema operacional não suportado.")
    raise SystemExit(1)


def ensure_pipx() -> None:
    if command_exists("pipx"):
        return

    error(
        "pipx não encontrado. Instale o pipx e reinicie o terminal."
    )

    error(
        "No Windows, instale o Python pela loja do Windows, "
        "depois 'python3 -m pip install --user pipx' e "
        "'python3 -m pipx ensurepath'."
    )

    raise SystemExit(1)


def tko_installed() -> bool:
    result = run(
        ["pipx", "list"],
        check=False,
        capture_output=True,
    )

    return "package tko " in result.stdout


def setup_tko() -> None:
    step("Instalando/atualizando TKO")

    ensure_python()
    ensure_pipx()

    if tko_installed():
        run(["pipx", "upgrade", "tko"])
    else:
        run(["pipx", "install", "tko"])

    success("TKO pronto para uso")


def setup_basic() -> None:
    step("Configurando ambiente básico")

    install_vscode_extensions(
        [
            "usernamehw.errorlens",
            "bierner.markdown-preview-github-styles",
            "tamasfe.even-better-toml",
            "editorconfig.editorconfig",
        ]
    )

    success("Ambiente básico configurado")


def ensure_basic() -> None:
    if tko_installed():
        return

    setup_tko()
    setup_basic()


# ============================================================
# Python
# ============================================================

def setup_python() -> None:
    ensure_basic()
    ensure_python()

    step("Configurando Python")

    write_if_missing(
        ".vscode/settings.json",
        """{
  "python.analysis.typeCheckingMode": "strict",
  "python.analysis.diagnosticMode": "workspace"
}""",
    )

    install_vscode_extensions(
        ["ms-python.python"]
    )

    success("Ambiente Python configurado")


# ============================================================
# TypeScript
# ============================================================

def setup_typescript() -> None:
    ensure_basic()

    step("Configurando TypeScript")

    install_global_npm(
        [
            "typescript",
            "esbuild",
        ]
    )

    run(
        [
            "npm",
            "install",
            "--save-dev",
            "@types/node",
            "readline-sync",
        ],
        check=False,
    )

    success("Ambiente TypeScript configurado")


# ============================================================
# Go
# ============================================================

def ensure_sudo_for_go() -> None:
    if is_writable("/usr/local"):
        return

    if not command_exists("sudo"):
        error(
            "sudo não encontrado. A instalação do Go requer "
            "acesso para gravar em /usr/local."
        )

        raise SystemExit(1)


def setup_go() -> None:
    ensure_basic()

    step(f"Instalando Go {GO_VERSION}")

    if platform.system() != "Linux":
        error(
            "A instalação automática do Go só é suportada "
            "em Linux/WSL."
        )
        return

    ensure_sudo_for_go()

    temporary = (
        Path(tempfile.gettempdir()) / GO_TAR
    )

    print(
        f"{GREEN}-> baixando {GO_URL}{RESET}"
    )

    download(
        GO_URL,
        temporary,
    )

    print(
        f"{GREEN}-> remover versão anterior do Go{RESET}"
    )

    run(
        [
            "sudo",
            "rm",
            "-rf",
            "/usr/local/go",
        ]
    )

    print(
        f"{GREEN}-> instalar {GO_TAR} em /usr/local{RESET}"
    )

    run(
        [
            "sudo",
            "tar",
            "-C",
            "/usr/local",
            "-xzf",
            str(temporary),
        ]
    )

    temporary.unlink(missing_ok=True)

    ensure_path_export(
        Path.home() / ".profile"
    )

    ensure_path_export(
        Path.home() / ".bashrc"
    )

    install_vscode_extensions(
        ["golang.Go"]
    )

    success("Ambiente Go configurado")


# ============================================================
# C/C++
# ============================================================

def setup_c() -> None:
    ensure_basic()

    step("Configuração C/C++")

    if not command_exists("apt"):
        error(
            "apt não encontrado. Configuração C/C++ só é "
            "suportada em sistemas baseados em Debian/Ubuntu "
            "(incluindo WSL)."
        )
        return

    run(["sudo", "apt", "update"])

    run(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "build-essential",
            "gdb",
        ]
    )

    install_vscode_extensions(
        ["ms-vscode.cpptools"]
    )

    success("Ambiente C/C++ configurado")


# ============================================================
# Java
# ============================================================

def setup_java() -> None:
    ensure_basic()

    step("Configuração Java")

    if not command_exists("apt"):
        error(
            "apt não encontrado. Configuração Java só é "
            "suportada em sistemas baseados em Debian/Ubuntu "
            "(incluindo WSL)."
        )
        return

    run(["sudo", "apt", "update"])

    run(
        [
            "sudo",
            "apt",
            "install",
            "-y",
            "openjdk-17-jdk",
        ]
    )

    install_vscode_extensions(
        ["vscjava.vscode-java-pack"]
    )

    success("Ambiente Java configurado")


# ============================================================
# Atualização dos scripts
# ============================================================

def update_scripts() -> None:
    step("Atualizando scripts")

    print(
        f"{GREEN}-> Atualizando git-sync.py{RESET}"
    )

    download(
        GITSYNC_URL,
        "git-sync.py",
    )

    Path("git-sync.py").chmod(0o755)

    print(
        f"{GREEN}-> Atualizando setup.py{RESET}"
    )

    download(
        SETUP_URL,
        "setup.py",
    )

    Path("setup.py").chmod(0o755)

    success("Scripts atualizados")


# ============================================================
# Programa principal
# ============================================================

def main() -> None:
    setup_functions = {
        "1": setup_tko,
        "2": update_scripts,
        "3": setup_python,
        "4": setup_c,
        "5": setup_typescript,
        "6": setup_go,
        "7": setup_java,
    }

    show_menu()

    choice = input("Escolha [1-7]: ").strip()

    setup = setup_functions.get(choice)

    if setup is None:
        error("Opção inválida")
        raise SystemExit(1)

    setup()

    print(
        f"\n{GREEN}{BOLD}"
        "Setup concluído."
        f"{RESET}"
    )


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        error(
            f"Comando falhou com código {exc.returncode}"
        )
        raise SystemExit(exc.returncode) from exc
    except KeyboardInterrupt:
        print()
        error("Operação cancelada pelo usuário")
        raise SystemExit(130) from None
