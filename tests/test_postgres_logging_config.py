"""Testes de validação estática da configuração de logs do PostgreSQL no Docker Compose."""

import re
import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
ARQUIVOS_COMPOSE = [
    "docker-compose.yml",
    "docker-compose.prod.yml",
]

VOLUME_LOGS_POSTGRES = "./containers/logs/postgres:/var/log/postgresql"

PARAMETROS_ESSENCIAIS_POSTGRES = [
    "shared_preload_libraries=pg_stat_statements,auto_explain",
    "logging_collector=on",
    "log_destination=stderr,jsonlog",
    "log_directory=/var/log/postgresql",
    "log_filename=postgresql-week-%V",
    "log_rotation_age=7d",
    "log_rotation_size=50MB",
    "log_file_mode=0644",
    "log_timezone=UTC",
    "log_lock_waits=on",
    "auto_explain.log_format=json",
]


def _carregar_servico_db(nome_arquivo: str) -> dict[str, Any]:
    """Carrega e retorna a definição do serviço `db` de um arquivo Docker Compose."""
    caminho_compose = RAIZ_PROJETO / nome_arquivo
    assert caminho_compose.is_file(), f"Arquivo não encontrado: {caminho_compose}"

    conteudo = yaml.safe_load(caminho_compose.read_text(encoding="utf-8"))
    assert isinstance(conteudo, dict), f"Estrutura YAML inválida em {nome_arquivo}."

    servicos = conteudo.get("services")
    assert isinstance(servicos, dict) and "db" in servicos, (
        f"Serviço 'db' ausente em {nome_arquivo}."
    )
    return servicos["db"]


def _extrair_parametros_c(comando: Any) -> list[str]:
    """Extrai todos os argumentos passados após a flag `-c` no `command` do serviço `db`."""
    assert isinstance(comando, list) and comando, (
        "O campo 'command' do serviço 'db' deve ser uma lista não vazia."
    )
    assert comando[0] == "postgres", (
        f"O primeiro argumento de 'command' deve ser 'postgres', encontrado: {comando[0]!r}"
    )

    parametros: list[str] = []
    indice = 1
    while indice < len(comando):
        item = comando[indice]
        if item == "-c":
            assert indice + 1 < len(comando), (
                "Flag '-c' sem valor correspondente no 'command' do serviço 'db'."
            )
            parametros.append(str(comando[indice + 1]))
            indice += 2
        else:
            indice += 1
    return parametros


@pytest.mark.parametrize("nome_arquivo", ARQUIVOS_COMPOSE)
def test_servico_db_monta_volume_logs_postgres(nome_arquivo: str) -> None:
    """Garante que o serviço `db` monta o volume persistente de logs do PostgreSQL."""
    servico_db = _carregar_servico_db(nome_arquivo)
    volumes = servico_db.get("volumes", [])

    assert isinstance(volumes, list), f"'volumes' deve ser uma lista em {nome_arquivo}."
    assert VOLUME_LOGS_POSTGRES in volumes, (
        f"Volume '{VOLUME_LOGS_POSTGRES}' ausente no serviço 'db' de {nome_arquivo}."
    )


@pytest.mark.parametrize("nome_arquivo", ARQUIVOS_COMPOSE)
def test_servico_db_entrypoint_prepara_diretorio_logs(nome_arquivo: str) -> None:
    """Garante que o `entrypoint` do serviço `db` prepara `/var/log/postgresql` com `chown` para `postgres`."""
    servico_db = _carregar_servico_db(nome_arquivo)
    entrypoint = servico_db.get("entrypoint")

    assert entrypoint, f"'entrypoint' ausente no serviço 'db' de {nome_arquivo}."
    if isinstance(entrypoint, list):
        assert entrypoint[:2] == ["/bin/sh", "-c"], (
            f"'entrypoint' deve iniciar com ['/bin/sh', '-c'] em {nome_arquivo}."
        )
        script_entrypoint = " ".join(str(parte) for parte in entrypoint)
    else:
        script_entrypoint = str(entrypoint)

    assert "mkdir -p /var/log/postgresql" in script_entrypoint, (
        f"Criação de '/var/log/postgresql' ausente no entrypoint de {nome_arquivo}."
    )
    assert "chown -R postgres:postgres /var/log/postgresql" in script_entrypoint, (
        f"'chown -R postgres:postgres /var/log/postgresql' ausente no entrypoint de {nome_arquivo}."
    )
    assert "-mtime +28 -delete" in script_entrypoint, (
        f"Poda de logs acima de 28 dias ('-mtime +28 -delete') ausente no entrypoint de {nome_arquivo}."
    )
    assert "docker-entrypoint.sh" in script_entrypoint, (
        f"Delegação para 'docker-entrypoint.sh' ausente no entrypoint de {nome_arquivo}."
    )


@pytest.mark.parametrize("nome_arquivo", ARQUIVOS_COMPOSE)
def test_servico_db_possui_parametros_essenciais_de_log_e_telemetria(nome_arquivo: str) -> None:
    """Garante que o `command` do serviço `db` inclui todos os parâmetros essenciais de log e telemetria."""
    servico_db = _carregar_servico_db(nome_arquivo)
    parametros = _extrair_parametros_c(servico_db.get("command"))

    ausentes = [
        parametro
        for parametro in PARAMETROS_ESSENCIAIS_POSTGRES
        if parametro not in parametros
    ]
    assert not ausentes, (
        f"Parâmetros essenciais ausentes no 'command' do serviço 'db' em {nome_arquivo}: {ausentes}"
    )


def test_docker_compose_dev_possui_bloco_logging_json_file() -> None:
    """Garante que `docker-compose.yml` configura rotação de logs no driver `json-file` para o serviço `db`."""
    servico_db = _carregar_servico_db("docker-compose.yml")
    bloco_logging = servico_db.get("logging")

    assert isinstance(bloco_logging, dict), (
        "Bloco 'logging' ausente no serviço 'db' de docker-compose.yml."
    )
    assert bloco_logging.get("driver") == "json-file", (
        f"Driver de logging esperado 'json-file', encontrado: {bloco_logging.get('driver')!r}"
    )

    opcoes = bloco_logging.get("options")
    assert isinstance(opcoes, dict), (
        "Bloco 'logging.options' ausente no serviço 'db' de docker-compose.yml."
    )
    assert opcoes.get("max-size") == "50m", (
        f"Valor esperado para 'max-size' é '50m', encontrado: {opcoes.get('max-size')!r}"
    )
    assert str(opcoes.get("max-file")) == "3", (
        f"Valor esperado para 'max-file' é '3', encontrado: {opcoes.get('max-file')!r}"
    )


def test_makefile_contem_alvos_db_logs_db_stats_e_prepara_diretorio_no_up() -> None:
    """Garante que o Makefile declara db-logs e db-stats em .PHONY e cria containers/logs/postgres no up."""
    conteudo_makefile = (RAIZ_PROJETO / "Makefile").read_text(encoding="utf-8")
    linhas = conteudo_makefile.splitlines()

    linhas_phony = [linha for linha in linhas if linha.startswith(".PHONY:")]
    assert linhas_phony, "Linha '.PHONY:' ausente no Makefile."
    alvos_phony = set(re.findall(r"[a-zA-Z0-9_-]+", " ".join(linhas_phony)))
    assert "db-logs" in alvos_phony, "Alvo 'db-logs' ausente na diretiva '.PHONY:' do Makefile."
    assert "db-stats" in alvos_phony, "Alvo 'db-stats' ausente na diretiva '.PHONY:' do Makefile."

    assert re.search(r"^db-logs:", conteudo_makefile, re.MULTILINE), (
        "Definição do alvo 'db-logs:' ausente no Makefile."
    )
    assert re.search(r"^db-stats:", conteudo_makefile, re.MULTILINE), (
        "Definição do alvo 'db-stats:' ausente no Makefile."
    )

    bloco_up = re.search(
        r"^up:.*?(?=^[a-zA-Z0-9_-]+:|\Z)",
        conteudo_makefile,
        re.MULTILINE | re.DOTALL,
    )
    assert bloco_up is not None, "Definição do alvo 'up:' ausente no Makefile."
    assert "mkdir -p" in bloco_up.group(0) and "containers/logs/postgres" in bloco_up.group(0), (
        "O alvo 'up:' do Makefile deve criar 'containers/logs/postgres' via mkdir -p."
    )


def test_makefile_comandos_db_logs_dry_run_e_help_executam_com_sucesso() -> None:
    """Garante que `make -n db-logs` e `make help` executam com código de saída 0."""
    resultado_db_logs = subprocess.run(
        ["make", "-n", "db-logs"],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado_db_logs.returncode == 0, (
        f"`make -n db-logs` falhou com código {resultado_db_logs.returncode}: {resultado_db_logs.stderr}"
    )
    assert "containers/logs/postgres" in resultado_db_logs.stdout

    resultado_help = subprocess.run(
        ["make", "help"],
        cwd=RAIZ_PROJETO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultado_help.returncode == 0, (
        f"`make help` falhou com código {resultado_help.returncode}: {resultado_help.stderr}"
    )
    assert "db-logs" in resultado_help.stdout
    assert "db-stats" in resultado_help.stdout


def test_documentacao_ports_e_cheatsheet_registra_observabilidade_postgres_e_sem_links_locais() -> None:
    """Garante atualização documental em ports/README.md e docker_cheatsheet.md sem links file:// ou /home/."""
    readme_ports = (RAIZ_PROJETO / "src" / "ports" / "README.md").read_text(encoding="utf-8")
    cheatsheet = (RAIZ_PROJETO / "docs" / "docker_cheatsheet.md").read_text(encoding="utf-8")

    assert "application_name" in readme_ports, (
        "Documentação de 'application_name' ausente em src/ports/README.md."
    )
    assert "pg_stat_statements" in readme_ports, (
        "Documentação de 'pg_stat_statements' ausente em src/ports/README.md."
    )

    assert "containers/logs/postgres" in cheatsheet, (
        "Documentação de 'containers/logs/postgres' ausente em docs/docker_cheatsheet.md."
    )
    assert "postgresql-week-%V" in cheatsheet, (
        "Documentação de 'postgresql-week-%V' (rotação 7 em 7 dias) ausente em docs/docker_cheatsheet.md."
    )
    assert "30 dias" in cheatsheet, (
        "Documentação da retenção de '30 dias' ausente em docs/docker_cheatsheet.md."
    )
    assert "pg_stat_statements" in cheatsheet, (
        "Documentação de 'pg_stat_statements' ausente em docs/docker_cheatsheet.md."
    )

    for caminho_relativo, conteudo in [
        ("src/ports/README.md", readme_ports),
        ("docs/docker_cheatsheet.md", cheatsheet),
    ]:
        assert "file://" not in conteudo, (
            f"Ocorrência proibida de 'file://' encontrada em {caminho_relativo}."
        )
        assert "/home/" not in conteudo, (
            f"Caminho absoluto '/home/' proibido encontrado em {caminho_relativo}."
        )
