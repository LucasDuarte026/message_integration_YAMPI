#!/usr/bin/env bash
# Orquestrador DevSecOps do projeto Message Integration.
# Executa auditorias automatizadas em 4 camadas:
#   1. secrets : TruffleHog (histórico Git e arquivos do projeto)
#   2. sast    : Semgrep (análise estática Python, Flask, SQL e segredos)
#   3. infra   : Trivy (dependências Python, Dockerfile e Docker Compose)
#   4. skills  : SkillSpector (auditoria de skills de agentes contra prompt injection)

set -euo pipefail

export PATH="/home/luska/.local/bin:$PATH"

RAIZ_PROJETO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ_PROJETO"

MODO="${1:-all}"
FALHAS=0

verificar_binario() {
    local binario="$1"
    if ! command -v "$binario" >/dev/null 2>&1; then
        echo "[ERRO] Binário '$binario' não encontrado no PATH (/home/luska/.local/bin)." >&2
        return 1
    fi
}

imprimir_cabecalho() {
    local titulo="$1"
    echo ""
    echo "========================================================================"
    echo " $titulo"
    echo "========================================================================"
}

executar_secrets() {
    imprimir_cabecalho "1/4 [TruffleHog] Varredura de Segredos no Histórico Git e Arquivos"
    verificar_binario "trufflehog" || return 1

    local commit_base="HEAD~20"
    if ! git rev-parse --verify "$commit_base" >/dev/null 2>&1; then
        commit_base="$(git rev-list --max-parents=0 HEAD | tail -n 1)"
    fi

    echo "-> Analisando histórico Git a partir de $commit_base (apenas credenciais verificadas)..."
    trufflehog git file://. \
        --since-commit "$commit_base" \
        --only-verified \
        --fail || return 1

    echo "-> Analisando arquivos locais de código, scripts e infraestrutura..."
    trufflehog filesystem \
        src/ scripts/ tests/ Dockerfile docker-compose.yml docker-compose.prod.yml \
        --only-verified \
        --fail || return 1

    echo "[OK] TruffleHog concluído sem segredos ativos vazados."
}

executar_sast() {
    imprimir_cabecalho "2/4 [Semgrep] Análise Estática de Código (SAST)"
    verificar_binario "semgrep" || return 1

    echo "-> Analisando src/ e scripts/ com regras p/python, p/flask e p/secrets..."
    semgrep scan \
        --config p/python \
        --config p/flask \
        --config p/secrets \
        --error \
        --exclude ".venv" \
        --exclude ".agents*" \
        --exclude "agents_corporativo*" \
        src/ scripts/ || return 1

    echo "[OK] Semgrep concluído sem vulnerabilidades bloqueantes."
}

executar_infra() {
    imprimir_cabecalho "3/4 [Trivy] Varredura de Dependências, Dockerfile e Compose"
    verificar_binario "trivy" || return 1

    local trivy_cache="$HOME/.cache/trivy"
    local espaco_livre_mb
    espaco_livre_mb="$(df -Pm "$HOME" | awk 'NR==2 {print $4}')"

    if [ "$espaco_livre_mb" -lt 2200 ] && [ ! -f "$HOME/.cache/trivy/db/trivy.db" ]; then
        trivy_cache="/dev/shm/trivy-cache"
        export TMPDIR="/dev/shm"
        echo "[AVISO] Espaço livre em $HOME (${espaco_livre_mb} MB) abaixo de 2200 MB."
        echo "[AVISO] Utilizando cache temporário em RAM ($trivy_cache) para a base de CVEs."
    fi

    echo "-> Verificando vulnerabilidades (HIGH/CRITICAL) e segredos em requirements.txt..."
    trivy fs \
        --cache-dir "$trivy_cache" \
        --scanners vuln,secret \
        --severity HIGH,CRITICAL \
        --ignore-unfixed \
        --exit-code 1 \
        requirements.txt || return 1

    echo "-> Verificando misconfigurations e segredos em Dockerfile e Compose..."
    local arquivo_infra
    for arquivo_infra in Dockerfile docker-compose.yml docker-compose.prod.yml; do
        echo "   [Trivy] Inspecionando $arquivo_infra (exibindo HIGH/CRITICAL)..."
        trivy fs \
            --cache-dir "$trivy_cache" \
            --scanners misconfig,secret \
            --severity HIGH,CRITICAL \
            "$arquivo_infra" || return 1
        trivy fs \
            --cache-dir "$trivy_cache" \
            --scanners misconfig,secret \
            --severity CRITICAL \
            --exit-code 1 \
            --quiet \
            "$arquivo_infra" || return 1
    done

    echo "[OK] Trivy concluído sem vulnerabilidades/falhas CRITICAL bloqueantes."
}

executar_skills() {
    imprimir_cabecalho "4/4 [SkillSpector] Auditoria de Segurança das Skills de Agentes"
    verificar_binario "skillspector" || return 1

    echo "-> Auditando a skill version_control com baseline verificado (--no-llm)..."
    skillspector scan .agents/skills/version_control \
        --no-llm \
        --baseline .agents/skills/version_control/.skillspector-baseline.yaml \
        --fail-on-findings || return 1

    echo "[OK] SkillSpector concluído sem riscos ativos na skill version_control."
}

rodar_etapa() {
    local nome_etapa="$1"
    local funcao_etapa="$2"

    if ! "$funcao_etapa"; then
        echo "[FALHA] A etapa '$nome_etapa' encontrou problemas críticos." >&2
        FALHAS=$((FALHAS + 1))
    fi
}

case "$MODO" in
    secrets)
        rodar_etapa "secrets (TruffleHog)" executar_secrets
        ;;
    sast)
        rodar_etapa "sast (Semgrep)" executar_sast
        ;;
    infra)
        rodar_etapa "infra (Trivy)" executar_infra
        ;;
    skills)
        rodar_etapa "skills (SkillSpector)" executar_skills
        ;;
    quick)
        rodar_etapa "secrets (TruffleHog)" executar_secrets
        rodar_etapa "sast (Semgrep)" executar_sast
        rodar_etapa "skills (SkillSpector)" executar_skills
        ;;
    all)
        rodar_etapa "secrets (TruffleHog)" executar_secrets
        rodar_etapa "sast (Semgrep)" executar_sast
        rodar_etapa "infra (Trivy)" executar_infra
        rodar_etapa "skills (SkillSpector)" executar_skills
        ;;
    *)
        echo "Uso: $0 {all|quick|secrets|sast|infra|skills}" >&2
        exit 2
        ;;
esac

echo ""
echo "========================================================================"
if [ "$FALHAS" -eq 0 ]; then
    echo " RESULTADO DEVSECOPS: APROVADO (todas as etapas solicitadas passaram)"
    echo "========================================================================"
    exit 0
else
    echo " RESULTADO DEVSECOPS: REPROVADO ($FALHAS etapa(s) com falhas)"
    echo "========================================================================"
    exit 1
fi
