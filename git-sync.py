#!/usr/bin/env python3

from __future__ import annotations

import datetime
import re
import signal
import subprocess
import sys
from pathlib import Path


# ============================================================
# Configuração
# ============================================================

ALLOWED_BRANCH = "main"
REMOTE = "origin"

LOG_DIR = Path(".git_logs")

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
BOLD = "\033[1m"
RESET = "\033[0m"

ANSI_ESCAPE = re.compile(r"\x1B\[[0-9;]*[mK]")


# ============================================================
# Exceções
# ============================================================


class GitError(RuntimeError):
    """Erro durante uma operação Git."""


class UserCancelled(Exception):
    """Operação cancelada pelo usuário."""


# ============================================================
# Console
# ============================================================


class Console:
    """Responsável pela saída e interação com o usuário."""

    def __init__(self, log_file: Path) -> None:
        self.log_file = log_file
        self.log_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def write(self, message: str = "") -> None:
        print(message)

        clean_message = ANSI_ESCAPE.sub(
            "",
            message,
        )

        with self.log_file.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(clean_message + "\n")

    def step(self, message: str) -> None:
        self.write(
            f"\n{BLUE}{BOLD}==>{RESET} "
            f"{BOLD}{message}{RESET}"
        )

    def success(self, message: str) -> None:
        self.write(
            f"{GREEN}[OK]{RESET} {message}"
        )

    def warn(self, message: str) -> None:
        self.write(
            f"{YELLOW}[AVISO]{RESET} {message}"
        )

    def error(self, message: str) -> None:
        self.write(
            f"{RED}[ERRO]{RESET} {message}"
        )

    def command(self, command: str) -> None:
        self.write(
            f"{GREEN}-> {command}{RESET}"
        )

    def ask(self, prompt: str) -> str:
        return input(prompt)

    def confirm(self, prompt: str) -> bool:
        answer = self.ask(
            f"{prompt} [Y/n] (Enter confirma): "
        )

        return answer.strip().lower() in {
            "",
            "y",
            "yes",
            "s",
            "sim",
        }


# ============================================================
# GitRepository
# ============================================================


class GitRepository:
    """
    Abstração sobre o repositório Git.

    Esta classe concentra todas as chamadas ao executável
    git. A lógica do fluxo da aplicação fica em SyncApplication.
    """

    def __init__(
        self,
        console: Console,
        executable: str = "git",
    ) -> None:
        self.console = console
        self.executable = executable

    # --------------------------------------------------------
    # Execução
    # --------------------------------------------------------

    def run(
        self,
        *args: str,
        check: bool = True,
        capture_output: bool = False,
        color: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        command = [self.executable, "--no-pager", *args]

        display_command = " ".join(command)

        self.console.command(display_command)

        if color:
            command = [
                self.executable,
                "--no-pager",
                "-c",
                "color.ui=always",
                *args,
            ]

        result = subprocess.run(
            command,
            text=True,
            capture_output=capture_output,
            check=False,
        )

        if capture_output:
            if result.stdout:
                self.console.write(
                    result.stdout.rstrip()
                )

            if result.stderr:
                self.console.write(
                    result.stderr.rstrip()
                )

        if check and result.returncode != 0:
            stderr = result.stderr.strip()

            if stderr:
                raise GitError(
                    f"{display_command}\n{stderr}"
                )

            raise GitError(
                f"Comando falhou "
                f"({result.returncode}): "
                f"{display_command}"
            )

        return result

    def output(self, *args: str) -> str:
        result = self.run(
            *args,
            capture_output=True,
        )

        return result.stdout.strip()

    def succeeds(self, *args: str) -> bool:
        result = self.run(
            *args,
            check=False,
        )

        return result.returncode == 0

    # --------------------------------------------------------
    # Repositório
    # --------------------------------------------------------

    def is_repository(self) -> bool:
        return self.succeeds(
            "rev-parse",
            "--is-inside-work-tree",
        )

    def current_branch(self) -> str:
        branch = self.output(
            "rev-parse",
            "--abbrev-ref",
            "HEAD",
        )

        if branch == "HEAD":
            raise GitError(
                "Você está em HEAD destacado."
            )

        return branch

    def has_remote(
        self,
        remote: str = REMOTE,
    ) -> bool:
        return self.succeeds(
            "remote",
            "get-url",
            remote,
        )

    # --------------------------------------------------------
    # Merge
    # --------------------------------------------------------

    def is_merge_in_progress(self) -> bool:
        return self.succeeds(
            "rev-parse",
            "-q",
            "--verify",
            "MERGE_HEAD",
        )

    def conflicted_files(self) -> list[str]:
        output = self.output(
            "diff",
            "--name-only",
            "--diff-filter=U",
        )

        return [
            file
            for file in output.splitlines()
            if file.strip()
        ]

    def has_conflicts(self) -> bool:
        return bool(
            self.conflicted_files()
        )

    # --------------------------------------------------------
    # Alterações
    # --------------------------------------------------------

    def has_unstaged_changes(self) -> bool:
        return not self.succeeds(
            "diff",
            "--quiet",
        )

    def has_staged_changes(self) -> bool:
        return not self.succeeds(
            "diff",
            "--cached",
            "--quiet",
        )

    def has_local_changes(self) -> bool:
        return (
            self.has_unstaged_changes()
            or self.has_staged_changes()
        )

    def status(self) -> None:
        self.run(
            "status",
            "--short",
            color=True,
            check=False,
        )

    def stage_all(self) -> None:
        self.run("add", "-A")

    def staged_diff_stat(self) -> None:
        self.run(
            "diff",
            "--cached",
            "--stat",
            color=True,
        )

    # --------------------------------------------------------
    # Commits
    # --------------------------------------------------------

    def commit(self, message: str) -> None:
        self.run(
            "commit",
            "-m",
            message,
        )

    def commit_merge(self) -> None:
        self.run(
            "commit",
            "--no-edit",
        )

    # --------------------------------------------------------
    # Resolução de conflitos
    # --------------------------------------------------------

    def checkout_ours(
        self,
        file: str,
    ) -> None:
        self.run(
            "checkout",
            "--ours",
            "--",
            file,
        )

        self.run(
            "add",
            file,
        )

    def checkout_theirs(
        self,
        file: str,
    ) -> None:
        self.run(
            "checkout",
            "--theirs",
            "--",
            file,
        )

        self.run(
            "add",
            file,
        )

    # --------------------------------------------------------
    # Remote / sincronização
    # --------------------------------------------------------

    def fetch(
        self,
        remote: str = REMOTE,
    ) -> None:
        self.run(
            "fetch",
            remote,
        )

    def remote_has_updates(
        self,
        branch: str,
        remote: str = REMOTE,
    ) -> bool:
        output = self.output(
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{remote}/{branch}",
        )

        parts = output.split()

        if len(parts) != 2:
            raise GitError(
                "Não foi possível determinar "
                "a diferença entre o repositório "
                "local e o remoto."
            )

        _, behind = parts

        return int(behind) > 0

    def merge_fast_forward(
        self,
        remote_branch: str,
    ) -> bool:
        result = self.run(
            "merge",
            "--ff-only",
            remote_branch,
            check=False,
        )

        return result.returncode == 0

    def merge(
        self,
        remote_branch: str,
    ) -> bool:
        result = self.run(
            "merge",
            remote_branch,
            check=False,
        )

        return result.returncode == 0

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    def has_upstream(self) -> bool:
        return self.succeeds(
            "rev-parse",
            "--abbrev-ref",
            "--symbolic-full-name",
            "@{u}",
        )

    def has_commits_to_push(self) -> bool:
        if not self.has_upstream():
            return True

        count = self.output(
            "rev-list",
            "--count",
            "@{u}..HEAD",
        )

        return int(count) > 0

    def push(
        self,
        branch: str,
        remote: str = REMOTE,
    ) -> None:
        if self.has_upstream():
            self.run("push")
            return

        self.run(
            "push",
            "-u",
            remote,
            branch,
        )

    # --------------------------------------------------------
    # Configuração
    # --------------------------------------------------------

    def get_config(
        self,
        key: str,
    ) -> str:
        result = self.run(
            "config",
            "--get",
            key,
            check=False,
            capture_output=True,
        )

        if result.returncode != 0:
            return ""

        return result.stdout.strip()

    def set_config(
        self,
        key: str,
        value: str,
    ) -> None:
        self.run(
            "config",
            key,
            value,
        )


# ============================================================
# SyncApplication
# ============================================================


class SyncApplication:
    """Orquestra o processo de sincronização."""

    def __init__(
        self,
        repository: GitRepository,
        console: Console,
        allowed_branch: str = ALLOWED_BRANCH,
    ) -> None:
        self.repository = repository
        self.console = console
        self.allowed_branch = allowed_branch

    # --------------------------------------------------------
    # Validação
    # --------------------------------------------------------

    def validate_environment(self) -> None:
        self.console.step(
            "Validando ambiente"
        )

        if not self.repository.is_repository():
            raise GitError(
                "Esse diretório não é um "
                "repositório git."
            )

        self.console.success(
            "Repositório git detectado"
        )

    def validate_remote(self) -> None:
        self.console.step(
            "Verificando conexão com o servidor"
        )

        if not self.repository.has_remote():
            raise GitError(
                "Remote 'origin' não configurado."
            )

        self.console.success(
            "Conexão com servidor OK"
        )

    def validate_branch(self) -> str:
        branch = self.repository.current_branch()

        if branch != self.allowed_branch:
            raise GitError(
                f"Branch inválida: {branch}"
            )

        return branch

    # --------------------------------------------------------
    # Conflitos pendentes
    # --------------------------------------------------------

    def show_unresolved_conflicts(self) -> None:
        conflicts = (
            self.repository.conflicted_files()
        )

        if not conflicts:
            return

        self.console.step(
            "Conflitos de merge ainda não resolvidos"
        )

        self.console.warn(
            "Os seguintes arquivos precisam "
            "ser resolvidos manualmente:"
        )

        for file in conflicts:
            self.console.write(
                f"  - {file}"
            )

        self.console.write("")

        self.console.warn(
            "Resolva os conflitos nos arquivos "
            "acima e execute o programa novamente."
        )

    def check_pending_conflicts(self) -> None:
        """
        Conflitos existentes no início do programa
        nunca são resolvidos automaticamente.

        O aluno deve resolvê-los manualmente e
        executar novamente o programa.
        """

        if not self.repository.has_conflicts():
            return

        self.show_unresolved_conflicts()

        raise UserCancelled

    # --------------------------------------------------------
    # Identidade
    # --------------------------------------------------------

    def setup_git_identity(self) -> None:
        self.console.step(
            "Verificando identidade do git"
        )

        user_name = self.repository.get_config(
            "user.name"
        )

        user_email = self.repository.get_config(
            "user.email"
        )

        if not user_name:
            name = self.console.ask(
                "Digite seu nome: "
            )

            if not name.strip():
                raise GitError(
                    "O nome não pode ser vazio."
                )

            self.repository.set_config(
                "user.name",
                name,
            )

        if not user_email:
            email = self.console.ask(
                "Digite seu email: "
            )

            if not email.strip():
                raise GitError(
                    "O email não pode ser vazio."
                )

            self.repository.set_config(
                "user.email",
                email,
            )

        self.console.success(
            "Identidade git configurada"
        )

    # --------------------------------------------------------
    # Status
    # --------------------------------------------------------

    def show_status(self) -> None:
        self.console.step(
            "Resumo do repositório "
            "(?? = novo, M = modificado, "
            "D = deletado, UU = conflito)"
        )

        self.repository.status()

    # --------------------------------------------------------
    # Commit das alterações locais
    # --------------------------------------------------------

    def ask_commit_message(self) -> str:
        while True:
            message = self.console.ask(
                "Mensagem do commit: "
            )

            if not message.strip():
                self.console.error(
                    "A mensagem de commit "
                    "não pode ser vazia."
                )
                continue

            return message

    def commit_local_changes(self) -> None:
        self.console.step(
            "Verificando alterações locais"
        )

        if not self.repository.has_local_changes():
            self.console.success(
                "Nenhuma alteração local encontrada"
            )
            return

        if not self.console.confirm(
            "Deseja salvar essas alterações agora?"
        ):
            raise UserCancelled

        self.repository.stage_all()

        if not self.repository.has_staged_changes():
            self.console.warn(
                "Nenhuma alteração pronta para commit."
            )
            return

        self.console.warn(
            "Resumo das alterações:"
        )

        self.repository.staged_diff_stat()

        message = self.ask_commit_message()

        self.repository.commit(message)

        self.console.success(
            "Alterações salvas"
        )

    # --------------------------------------------------------
    # Resolução de conflitos recém-criados
    # --------------------------------------------------------

    def resolve_merge_conflicts(self) -> None:
        """
        Resolve conflitos que acabaram de ser criados
        pelo merge executado nesta execução.
        """

        self.console.step(
            "Conflitos detectados"
        )

        conflicts = (
            self.repository.conflicted_files()
        )

        for file in conflicts:
            self.console.write(
                f"Arquivo em conflito: {file}"
            )

            self.console.write(
                "1) Manter MINHA versão"
            )
            self.console.write(
                "2) Manter versão do SERVIDOR"
            )
            self.console.write(
                "3) Resolver manualmente"
            )

            choice = self.console.ask(
                "> "
            ).strip()

            if choice == "1":
                self.repository.checkout_ours(
                    file
                )

            elif choice == "2":
                self.repository.checkout_theirs(
                    file
                )

            elif choice == "3":
                self.console.write("")

                self.console.warn(
                    "Resolva manualmente os conflitos "
                    "nos arquivos abaixo:"
                )

                for conflict in conflicts:
                    self.console.write(
                        f"  - {conflict}"
                    )

                self.console.write("")

                self.console.warn(
                    "Depois de corrigir os arquivos, "
                    "execute o programa novamente."
                )

                raise UserCancelled

            else:
                self.console.warn(
                    "Opção inválida."
                )

                raise UserCancelled

        if self.repository.has_conflicts():
            raise GitError(
                "Ainda existem conflitos "
                "não resolvidos."
            )

        if self.repository.has_staged_changes():
            self.repository.commit(
                "resolve merge conflicts"
            )

        self.console.success(
            "Conflitos resolvidos"
        )

    # --------------------------------------------------------
    # Merge pendente
    # --------------------------------------------------------

    def handle_pending_merge(self) -> None:
        """
        Finaliza um merge iniciado anteriormente,
        desde que os conflitos já tenham sido
        resolvidos manualmente.
        """

        if not self.repository.is_merge_in_progress():
            return

        self.console.step(
            "Merge pendente detectado"
        )

        # Proteção adicional. Em condições normais,
        # check_pending_conflicts() já detectou isso.
        if self.repository.has_conflicts():
            self.show_unresolved_conflicts()
            raise UserCancelled

        self.repository.stage_all()

        if self.repository.has_staged_changes():
            self.repository.commit_merge()

        self.console.success(
            "Merge pendente finalizado"
        )

    # --------------------------------------------------------
    # Sincronização
    # --------------------------------------------------------

    def sync_with_remote(
        self,
        branch: str,
    ) -> None:
        self.console.step(
            "Baixando atualizações do servidor"
        )

        self.repository.fetch()

        if not self.repository.remote_has_updates(
            branch
        ):
            self.console.success(
                "Seu repositório já está atualizado"
            )
            return

        if not self.console.confirm(
            "Deseja continuar?"
        ):
            raise UserCancelled

        remote_branch = (
            f"{REMOTE}/{branch}"
        )

        # Primeiro tenta uma atualização sem merge.
        if self.repository.merge_fast_forward(
            remote_branch
        ):
            self.console.success(
                "Atualizações recebidas"
            )
            return

        self.console.warn(
            "Fast-forward não foi possível. "
            "Tentando merge."
        )

        # Agora pode ocorrer conflito.
        if self.repository.merge(
            remote_branch
        ):
            self.console.success(
                "Atualizações recebidas"
            )
            return

        # O conflito foi criado nesta execução.
        if self.repository.has_conflicts():
            self.resolve_merge_conflicts()
            return

        raise GitError(
            "Erro ao atualizar repositório."
        )

    # --------------------------------------------------------
    # Push
    # --------------------------------------------------------

    def push_changes(
        self,
        branch: str,
    ) -> None:
        self.console.step(
            "Enviando alterações para o servidor"
        )

        if not self.repository.has_commits_to_push():
            self.console.success(
                "Nenhum commit novo para enviar"
            )
            return

        self.repository.push(branch)

        self.console.success(
            "Alterações enviadas"
        )

    # --------------------------------------------------------
    # Resumo
    # --------------------------------------------------------

    def show_final_summary(self) -> None:
        self.console.step(
            "Resumo final"
        )

        self.console.write(
            f"{GREEN}✓{RESET} alterações salvas"
        )

        self.console.write(
            f"{GREEN}✓{RESET} repositório atualizado"
        )

        self.console.write(
            f"{GREEN}✓{RESET} alterações enviadas"
        )

        self.console.step(
            f"Log salvo em: "
            f"{self.console.log_file}"
        )

    # --------------------------------------------------------
    # Fluxo principal
    # --------------------------------------------------------

    def run(self) -> None:
        self.console.write(
            f"{BOLD}SYNC EDUCACIONAL GIT{RESET}"
        )

        # ----------------------------------------------------
        # 1. Ambiente
        # ----------------------------------------------------

        self.validate_environment()
        self.validate_remote()

        # ----------------------------------------------------
        # 2. IMPORTANTE:
        #    não iniciar operações se já houver
        #    conflitos pendentes.
        # ----------------------------------------------------

        self.check_pending_conflicts()

        # ----------------------------------------------------
        # 3. Configuração
        # ----------------------------------------------------

        self.setup_git_identity()

        branch = self.validate_branch()

        self.show_status()

        # ----------------------------------------------------
        # 4. Finalizar merge previamente resolvido
        # ----------------------------------------------------

        self.handle_pending_merge()

        # ----------------------------------------------------
        # 5. Salvar alterações locais
        # ----------------------------------------------------

        self.commit_local_changes()

        # ----------------------------------------------------
        # 6. Atualizar a partir do servidor
        # ----------------------------------------------------

        self.sync_with_remote(branch)

        # ----------------------------------------------------
        # 7. Enviar alterações
        # ----------------------------------------------------

        self.push_changes(branch)

        # ----------------------------------------------------
        # 8. Finalização
        # ----------------------------------------------------

        self.show_final_summary()

        self.console.write(
            f"{GREEN}{BOLD}"
            "Sync concluído com sucesso."
            f"{RESET}"
        )


# ============================================================
# Inicialização
# ============================================================


def create_application() -> SyncApplication:
    timestamp = datetime.datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    log_file = (
        LOG_DIR /
        f"{timestamp}.log"
    )

    console = Console(log_file)

    repository = GitRepository(
        console=console,
    )

    return SyncApplication(
        repository=repository,
        console=console,
    )


def handle_interrupt(
    _signum: int,
    _frame: object,
) -> None:
    print()

    print(
        f"{YELLOW}[AVISO]{RESET} "
        "Operação cancelada pelo usuário."
    )

    sys.exit(130)


def main() -> int:
    signal.signal(
        signal.SIGINT,
        handle_interrupt,
    )

    application = create_application()

    try:
        application.run()

    except UserCancelled:
        application.console.warn(
            "Operação cancelada."
        )
        return 0

    except GitError as exc:
        application.console.error(
            str(exc)
        )
        return 1

    except KeyboardInterrupt:
        application.console.warn(
            "Operação cancelada pelo usuário."
        )
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())