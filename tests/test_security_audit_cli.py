"""Testes de integração da infraestrutura DevSecOps e do gate na skill version_control."""

import os
import shutil
from pathlib import Path

RAIZ_PROJETO = Path(__file__).resolve().parent.parent
LOCAL_BIN = Path("/home/luska/.local/bin")

FERRAMENTAS_ESSENCIAIS = ("trivy", "trufflehog", "semgrep", "skillspector")
TARGETS_MAKEFILE = (
    "security-audit",
    "security-quick",
    "security-secrets",
    "security-sast",
    "security-infra",
    "security-skills",
)


def test_script_security_audit_existe_e_executavel() -> None:
    """Garante que o orquestrador scripts/security_audit.sh existe e tem permissão de execução."""
    caminho_script = RAIZ_PROJETO / "scripts" / "security_audit.sh"
    assert caminho_script.is_file(), "O script scripts/security_audit.sh não foi encontrado."
    assert os.access(caminho_script, os.X_OK), (
        "O script scripts/security_audit.sh não possui permissão de execução."
    )


def test_binarios_devsecops_instalados() -> None:
    """Garante que os 4 binários essenciais estão disponíveis em /home/luska/.local/bin ou no PATH."""
    path_composto = f"{LOCAL_BIN}:{os.environ.get('PATH', '')}"
    ausentes = [
        ferramenta
        for ferramenta in FERRAMENTAS_ESSENCIAIS
        if shutil.which(ferramenta, path=path_composto) is None
    ]
    assert not ausentes, f"Ferramentas essenciais ausentes: {', '.join(ausentes)}"


def test_makefile_possui_targets_de_seguranca() -> None:
    """Garante que o Makefile expõe todos os targets da suíte de segurança."""
    conteudo_makefile = (RAIZ_PROJETO / "Makefile").read_text(encoding="utf-8")
    faltantes = [
        target for target in TARGETS_MAKEFILE if f"{target}:" not in conteudo_makefile
    ]
    assert not faltantes, f"Targets ausentes no Makefile: {', '.join(faltantes)}"


def test_skill_version_control_integra_gate_devsecops() -> None:
    """Garante que SKILL.md e full_spec.md exigem make security-audit e citam as 4 ferramentas."""
    arquivos_skill = [
        RAIZ_PROJETO / ".agents" / "skills" / "version_control" / "SKILL.md",
        RAIZ_PROJETO
        / ".agents"
        / "skills"
        / "version_control"
        / "references"
        / "full_spec.md",
    ]
    nomes_esperados = ("make security-audit", "Trivy", "TruffleHog", "Semgrep", "SkillSpector")

    for caminho in arquivos_skill:
        conteudo = caminho.read_text(encoding="utf-8")
        faltantes = [item for item in nomes_esperados if item not in conteudo]
        assert not faltantes, (
            f"Referências obrigatórias ausentes em {caminho.name}: {', '.join(faltantes)}"
        )
