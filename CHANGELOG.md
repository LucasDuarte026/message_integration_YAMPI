# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [7.1.2] - 2026-11-25 (Carrossel Visual Full-Width v0, Benchmarks Auditados 2025–2026, Precisão de Polling & Evidências Sentry APM - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado (Vitrine Visual do README & Higiene do Repositório)
- **Carrossel Visual Full-Width no Topo do [`README.md`](./README.md) (`images/resume/`):**
  - Gerado o carrossel animado 24-bit [`images/resume/showcase_carousel.webp`](./images/resume/showcase_carousel.webp) (`1600×1000`, `20` frames, `loop=0`, `2.2 MB`) com as 5 pranchas de arquitetura e provas de produção (`hero_featured_1200x627.png` e `plate_1` a `plate_4`), inserido como primeiro elemento visual do `README.md` em largura máxima (`width="100%"`) compatível com o sanitizer HTML do GitHub.
  - Adicionada barra de navegação direta para cada prancha em alta resolução e galeria recolhível (`<details>`) exibindo todas as 5 imagens estáticas em `width="100%"`.
- **Higiene do Repositório ([`.gitignore`](./.gitignore)):**
  - Adicionado `research/` ao `.gitignore` para manter artefatos locais de pesquisa fora do rastreamento público.

### Alterado (Documentação, Rigor Estatístico & Evidências de Produção)
- **Endurecimento de Benchmarks 2025–2026 & Alinhamento Arquitetural ([`README.md`](./README.md)):**
  - Consolidados benchmarks globais e brasileiros com fontes auditadas 2025–2026: **Baymard Institute** (`70.22%`, 50 estudos), **Dynamic Yield** (`79.53%–80.45%` mobile vs. `68.62%–69.56%` desktop), **Opinion Box 2026** / **E-commerce Radar** (`79%–82%` Brasil, `82%` retorno via cupom, `27%` abandono por cupom quebrado), **Nuvemshop** (`49%` PIX), **Banco Central** (`55.2%`), **PagBrasil** (`~75%` conversão PIX), **Klaviyo 2026** (`3.33%` conversão média, `$6.77–$13.70` RPR, `~41%` da receita atribuída), **Validity 2026** (`87.2%` global, `89.0%` Brasil, `77.4%` Microsoft), **Microsoft Maio 2025 (`550 5.7.515`)**, **Gorgias** (`18%–33%` WISMO puro / `~51%` combinado, `$12.40` custo manual US) e **Deloitte Digital 2026** (`$7.80` custo global/contato).
  - Adicionado bloco recolhível **Audited Industry & RFC References (2025–2026)** com links primários (incluindo IETF RFC 5321 §6.1, RFC 5322, RFC 2046 e RFC 8058).
  - Corrigida a terminologia para refletir com exatidão o motor de **polling na API REST V2 da Yampi** com congelamento determinístico (`order_id IS NOT NULL`), idempotência de evento de negócio (`SELECT ... FOR UPDATE`) com semântica `at-least-once` de SMTP (RFC 5321 §6.1), e certificação estática de protocolo (`10/10` Mail-Tester) vs. colocação em caixa de entrada.
  - Removida menção de versão fixa na badge de release do `README.md` (`Release: STABLE`).
- **Atualização das Capturas de Produção (`images/sentry_dashboard.png` e `images/crontab.png`):**
  - Sincronizados os contadores e percentis no `README.md` com a janela contínua de produção (`1,041` iniciados, `1,030` submissões SMTP aceitas sem destinatários recusados, `0` issues não resolvidas, `397K` spans de I/O, `5.80s` P50 / `12.89s` P95).

## [7.1.1] - 2026-11-23 (Certificação de Entregabilidade 10/10, Conformidade SDD & Sanitização Documental - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado (Vitrine de Certificação & Compliance)
- **Certificação de Entregabilidade `10/10` e Matriz de Compliance ([`README.md`](./README.md) e `images/`):**
  - Adicionada a seção **`Email Deliverability Certification (10/10) & Anti-Spam Compliance`** com evidência visual ([`images/mail_tester_com.png`](./images/mail_tester_com.png)) comprovando nota **`10/10`** para ambos os fluxos (informativos/transacionais e promocionais).
  - Incluída matriz completa cobrindo `SPF (RFC 7208 -all)`, `DKIM (RFC 6376, 2048-bit RSA + Oversigning)`, `DMARC (RFC 7489, p=quarantine/p=reject sem ruf=)`, `One-Click Unsubscribe (RFC 8058 / RFC 2369)`, `Honor Unsubscribe & Spam Rate Gate (< 0,10%)`, `MIME (RFC 5322 / RFC 2046)`, `TLS / FCrDNS / rDNS / IP Reputation`, `SpamAssassin (-0.2) / Anti-Graymail` e isolamento dual SMTP.
  - Substituída a badge de segurança no topo do `README.md` pela badge **`Deliverability 10/10 Certified | RFC Compliant`**, simplificada a seção de governança de segurança e lastreados os benchmarks de mercado da introdução com fontes reais citadas (`Baymard Institute`, `Klaviyo`, `Validity` e `Gorgias`).

### Modificado (Conformidade SDD & Sanitização Documental)
- **Especificações SDD & Governança *Bulk Sender* ([`docs/email_deliverability_policies.md`](./docs/email_deliverability_policies.md) e [`docs/sdd_specs.md`](./docs/sdd_specs.md)):**
  - Consolidada a certificação DNS/antispam (`10/10` + Google Postmaster Tools) na Fase 5, `POL-EMAIL-05` e `REQ-12`.
  - Adicionado o requisito normativo **`POL-EMAIL-06`** definindo o gate obrigatório para *Bulk Senders* (`>= 5.000 e-mails/dia` no Gmail: endpoint `HTTPS POST` sem redirect/login com token opaco, supressão automática em até 48h e link visível no corpo HTML).
- **Sanitização Pública (`README.md`, `docs/*` e `CHANGELOG.md`):**
  - Removidas referências específicas de marca, contas de envio, provedores e sufixos internos na documentação pública, mantendo o código-fonte em produção (`src/`) intacto.

---

## [7.1.0] - 2026-11-22 (Observabilidade Estruturada PostgreSQL 15 & Application Metrics do Daemon no Sentry - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado (Observabilidade & Diagnóstico Interno SQL / PostgreSQL 15)
- **Logs Estruturados e Planos de Execução em Container ([`docker-compose.yml`](./docker-compose.yml) e [`docker-compose.prod.yml`](./docker-compose.prod.yml))**:
  - Configurado coletor persistente (`logging_collector=on`) gravando saída dupla nativa do PostgreSQL 15 (`stderr,jsonlog` — arquivos `.log` e `.json`) em `./containers/logs/postgres:/var/log/postgresql`, com preparação automática de permissão no boot (`UID 70` / `postgres:postgres` e `log_file_mode=0644`) compatível com `no-new-privileges:true`.
  - Configurada rotação semanal de **7 em 7 dias** (`log_filename=postgresql-week-%V`, `log_rotation_age=7d`, `log_rotation_size=50MB`, `log_truncate_on_rotation=on`) com poda automática no `entrypoint` para arquivos acima de 28 dias, mantendo retenção circular de 4 arquivos semanais (~30 dias) em UTC.
  - Ativado diagnóstico SQL para futuras otimizações: `shared_preload_libraries=pg_stat_statements,auto_explain`, rastreamento de queries lentas (`>= 200ms` + amostragem de 10% acima de `50ms`), auditoria de DDL (`log_statement=ddl`), contenção de locks (`log_lock_waits=on`, `deadlock_timeout=1s`), arquivos temporários (`log_temp_files=0`), checkpoints, autovacuum lento e planos de execução JSON automáticos via `auto_explain` (`>= 500ms`, com buffers e WAL).
- **Identificação de Conexões & Estatísticas Agregadas ([`src/ports/postgres_repo.py`](./src/ports/postgres_repo.py) e [`src/ports/README.md`](./src/ports/README.md))**:
  - Pool `ThreadedConnectionPool` agora identifica as sessões com `application_name="message_integration_app"` para rastreio nos logs JSON do PostgreSQL 15.
  - `_init_db()` habilita de forma resiliente `CREATE EXTENSION IF NOT EXISTS pg_stat_statements;` após o commit principal das tabelas/índices, executando `rollback()` e `logger.warning` em caso de indisponibilidade sem interromper a aplicação.
- **Atalhos Consultivos e Documentação Operacional ([`Makefile`](./Makefile) e [`docs/docker_cheatsheet.md`](./docs/docker_cheatsheet.md))**:
  - Adicionados os alvos `make db-logs` (inspeção dos logs `.json` e `.log` em `containers/logs/postgres/`) e `make db-stats` (consulta top-15 de queries em `pg_stat_statements` usando `$POSTGRES_USER` e `$POSTGRES_DB` internos do container `db`), além de ajuste tolerante no `make up` para diretórios criados pelo daemon Docker.

### Adicionado (Telemetria do Ciclo do Daemon no Sentry)
- **Métricas de Execução e Latência de `yampi-daemon-cycle` ([`src/core/telemetry.py`](./src/core/telemetry.py), [`src/daemon.py`](./src/daemon.py) e [`src/core/README.md`](./src/core/README.md))**:
  - Adicionadas as constantes `METRIC_DAEMON_CYCLE_COMPLETED` (`daemon.cycle.completed`) e `METRIC_DAEMON_CYCLE_DURATION` (`daemon.cycle.duration`) e o helper Zero-Crash `record_daemon_cycle_metrics()`.
  - `src/daemon.py` mede o tempo de cada ciclo via `time.perf_counter()`, emitindo o contador (`status="ok"` ou `"error"`) e a distribuição de duração em segundos com `monitor.slug="yampi-daemon-cycle"` (mais `flush_telemetry()` em exceções), mantendo intacto o único Cron Monitor do plano Sentry e liberando a plotagem no Custom Dashboard via dataset *Application Metrics*.

### Adicionado (Testes)
- **Suíte de Testes Expandida ([`tests/test_postgres_logging_config.py`](./tests/test_postgres_logging_config.py), [`tests/test_postgres_repo_pool.py`](./tests/test_postgres_repo_pool.py) e [`tests/test_main_and_daemon.py`](./tests/test_main_and_daemon.py))**:
  - Adicionados 17 novos testes cobrindo infraestrutura Compose, Makefile, documentação sem links locais, `application_name`, `pg_stat_statements` e métricas do daemon (`140 passed` no total).

## [7.0.0] - 2026-11-21 (Lançamento Oficial Major v7.0.0: Vitrine Visual de Observabilidade Sentry APM & Crons, Governança Enterprise GitHub, Suíte DevSecOps 4 Camadas e Telemetria Semântica `email.type` - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado (Vitrine Visual & Observabilidade Sentry APM / Crons)
- **Documentação Visual de Observabilidade em Produção ([`README.md`](./README.md) e `images/`)**:
  - Incorporados os painéis reais de produção ([`images/sentry_dashboard.png`](./images/sentry_dashboard.png) e [`images/crontab.png`](./images/crontab.png)) ilustrando os contadores em tempo real (`email.dispatch.started`, `email.dispatch.sent`, `email.dispatch.failed`), percentis de latência `P50` / `P95`, decomposição categórica pela dimensão semântica `email.type` (9 tipos canônicos) e monitoramento contínuo de heartbeat do daemon (`yampi-daemon-cycle` via `sentry_sdk.crons.monitor`).
  - Documentadas em detalhe as camadas de conformidade LGPD Zero-PII (`send_default_pii=False`, `_mask_email()`, extração exclusiva de `email.recipient_domain` e `_build_pii_sanitizer_processor()`).

### Adicionado (Governança Enterprise do Repositório GitHub)
- **Controle de Estatísticas Linguist & Diffs ([`.gitattributes`](./.gitattributes))**:
  - Configurada normalização automática de fim de linha (`* text=auto eol=lf`), exclusão de templates compilados (`src/templates/emails/html_compiled/*.html`, `mjml/*.mjml`), exports do grafo (`graphify-out/**`) e imagens (`images/**`) da barra de linguagens via `linguist-generated=true`, marcação de documentações com `linguist-documentation=true` e skills com `linguist-vendored=true`.
- **Política de Segurança & Templates GitHub ([`SECURITY.md`](./SECURITY.md) e [`.github/`](./.github/))**:
  - Criada a política oficial de reporte privado de vulnerabilidades e garantias LGPD em [`SECURITY.md`](./SECURITY.md).
  - Adicionados formulários estruturados de Issues ([`bug_report.yml`](./.github/ISSUE_TEMPLATE/bug_report.yml), [`feature_request.yml`](./.github/ISSUE_TEMPLATE/feature_request.yml), [`config.yml`](./.github/ISSUE_TEMPLATE/config.yml)), checklist de governança para Pull Requests ([`pull_request_template.md`](./.github/pull_request_template.md)) e categorização automática de Release Notes ([`release.yml`](./.github/release.yml)).

### Modificado (Padronização Internacional & Consolidação v7.0.0)
- **Vitrine Principal 100% em Inglês ([`README.md`](./README.md))**:
  - Unificado todo o `README.md` sob o posicionamento *Engineering & Conversion Authority* (removendo blocos remanescentes em PT-BR e sinalizando documentos externos com badge `[PT-BR]`), com sumário navegável (*Table of Contents*), tabela completa dos 21 alvos do [`Makefile`](./Makefile) e documentação da Suíte DevSecOps em 4 camadas (`TruffleHog`, `Semgrep`, `Trivy`, `SkillSpector`).
  - Atualizados os metadados de versão para a linha oficial **`7.0.0`** (`VERSION`, badges de release no `README.md` e versões suportadas em `SECURITY.md`).

---

## [6.8.0] - 2026-11-21 (Suíte DevSecOps Automatizada Pré-Push e Tag Semântica `email.type` na Telemetria Sentry - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado (Segurança & DevSecOps)
- **Orquestração Automatizada em 4 Camadas ([`scripts/security_audit.sh`](./scripts/security_audit.sh) e [`Makefile`](./Makefile))**:
  - Integrada a suíte DevSecOps com **TruffleHog** (varredura de segredos verificados no histórico Git e arquivos), **Semgrep** (SAST `p/python`, `p/flask`, `p/secrets` em `src/` e `scripts/`), **Trivy** (CVEs em `requirements.txt` com fallback automático de cache para `/dev/shm/trivy-cache` e inspeção de `Dockerfile` / `docker-compose*.yml`) e **SkillSpector** (auditoria de skills de agentes com baseline verificado).
  - Adicionados os alvos `security-audit`, `security-quick`, `security-secrets`, `security-sast`, `security-infra` e `security-skills` no [`Makefile`](./Makefile) e documentação correspondente em [`scripts/README.md`](./scripts/README.md).
  - Integrado o gate obrigatório pré-commit e pré-push na skill `version_control` e adicionada a suíte de validação [`tests/test_security_audit_cli.py`](./tests/test_security_audit_cli.py).

### Adicionado (Telemetria & Observabilidade Sentry)
- **Dimensão Semântica `email.type` nos Disparos de E-mail (`src/core/telemetry.py`, `src/domain/interfaces.py`, `src/ports/`, `src/services/notification_service.py`)**:
  - Adicionado o mapeamento canônico `EMAIL_TYPE_BY_TEMPLATE` e a função `resolve_email_type()` em `src/core/telemetry.py`.
  - Propagado `email.type` no contrato `MessageProviderProtocol`, no `DryRunMessageProvider`, nos spans `email.smtp.send`, *breadcrumbs* `smtp.retry`, métricas e capturas de erro do `SMTPEmailProvider` e nos fluxos de pedidos/carrinhos do `NotificationService`.
  - Atualizados os READMEs internos (`src/core/README.md`, `src/domain/README.md`, `src/ports/README.md`) e ampliados os testes em `tests/test_email_telemetry.py`, `tests/test_abandoned_cart.py` e `tests/test_orders.py` (`123 passed` na suíte completa).

---

## [6.7.0] - 2026-11-20 (Entregabilidade RFC 2046/5322/8058, Roteamento Dual SMTP, Otimização WebP e Telemetria Sentry Application Metrics - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado
- **Telemetria de Disparos de E-mail no Sentry (`src/core/telemetry.py`, `smtp_email_provider.py`, `notification_service.py`, `main.py`, `debug_main.py`)**:
  - Implementado o módulo central Zero-Crash `src/core/telemetry.py` com três contadores oficiais via `sentry_sdk.metrics.count`: `email.dispatch.started` (1x ao iniciar), `email.dispatch.sent` (imediatamente após `sendmail()` confirmar aceitação sem `refused` e antes do *throttling*) e `email.dispatch.failed` (em falhas de `template_build`, `smtp_retries_exhausted` ou `smtp_fatal`).
  - Adicionados spans `email.smtp.send` por tentativa SMTP (`start_smtp_span`), *breadcrumbs* `smtp.retry` (`add_smtp_retry_breadcrumb`), isolamento thread-safe por disparo via `email_dispatch_scope` (`primary` vs `duplicate`, com `order_id`, `order_number`, `cart_id`, `template_name`, `stage` e `recipient_domain`), captura única de exceções preservando *traceback* completo + `retry_history` sanitizado e deduplicação automática (`DedupeIntegration` + `logger.warning` no `NotificationService`).
  - Aplicada defesa em profundidade LGPD (`_build_pii_sanitizer_processor` + `_sanitize_frame_vars`) redigindo incondicionalmente variáveis locais sensíveis em `frame["vars"]` (HTML, `customer_data`, `event`, tokens) e múltiplos e-mails, além de `flush_telemetry()` em `_close_resources()` (`src/main.py`) e ao término de `src/debug_main.py`.
- **Roteamento Dual de Remetentes SMTP (`transactional@` vs. `promotions@`)**:
  - Configurados dois pools SMTP independentes no `SMTPEmailProvider` (`_server` para avisos transacionais e `_promo_server` via `PROMO_SMTP_USER`/`PROMO_SMTP_PASSWORD`/`PROMO_SMTP_FROM` para cupons e recuperação de carrinhos), protegidos por `threading.Lock`, com fallback transparente para `_server`, isolamento de falhas entre canais e encerramento de ambos em `close()`.
  - Suporte via `.env` / `Config` (`src/core/config.py`, `.env.example`) para `PROMO_SMTP_*`, `EMAIL_FROM_NAME`, `EMAIL_REPLY_TO`, `EMAIL_MESSAGE_ID_DOMAIN`, `EMAIL_UNSUBSCRIBE_URL`, `EMAIL_UNSUBSCRIBE_MAILTO` e `EMAIL_ASSETS_DIR`.
- **Modernização MIME & Entregabilidade (RFC 2046 / 5322 / 8058 e WebP Modular)**:
  - Migrado `SMTPEmailProvider` para `email.message.EmailMessage` com alternativa `text/plain` gerada por `_HTMLToPlainTextParser` / `build_with_plain_text()` (`src/services/email_builders/base_builder.py`) precedendo `text/html`, cabeçalhos `Message-ID`, `Date`, `From`, `Reply-To` e `List-Unsubscribe: One-Click` em fluxos promocionais, além de validação explícita de `refused` retornado por `sendmail()`.
  - Higienização lexical dos assuntos e templates (`brand_data.yml`, `src/templates/emails/mjml/`, `html_compiled/`), desativação do envio duplicado por padrão (`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = False`) contra *Graymail*, externalização dos ativos WebP otimizados (`EMAIL_ASSETS_DIR` + volume `/app/email_assets:ro` em `docker-compose.yml` / `docker-compose.prod.yml` + `.gitignore`) e remoção dos PNGs legados e mocks HTML do repositório.

### Testes e Qualidade
- **Expansão da Suíte Pytest (`107 passed`, `7 subtests`, `85%` de cobertura global em `src/`)**:
  - Adicionadas as suítes `tests/test_email_plain_text.py`, `tests/test_dual_sender_routing.py` e `tests/test_email_telemetry.py` (usando `DummyTransport` real do `sentry-sdk`, cobrindo `88%` em `telemetry.py`, `96%` em `smtp_email_provider.py` e `95%` em `notification_service.py`).
  - Atualizados `tests/test_abandoned_cart.py`, `tests/test_orders.py` e `tests/test_smtp_email_provider.py` para o novo contrato MIME, `plain_text` e `is_promotional`.

### Documentação e Conformidade SDD (Zero Doc-Drift)
- Adicionado [`docs/email_deliverability_policies.md`](./docs/email_deliverability_policies.md), os requisitos normativos `REQ-12`, `REQ-13` e `REQ-14` e as decisões `ADR-05` e `ADR-06` em [`docs/sdd_specs.md`](./docs/sdd_specs.md).
- Atualizados [`docs/sentry_dashboard_guide.md`](./docs/sentry_dashboard_guide.md) (catálogo de métricas, queries prontas, diagrama Mermaid e guia de reprodução), [`docs/architecture.md`](./docs/architecture.md), [`docs/project_overview.md`](./docs/project_overview.md), [`docs/project_dependency_tree.md`](./docs/project_dependency_tree.md), [`docs/testing_guidelines.md`](./docs/testing_guidelines.md), [`docs/README.md`](./docs/README.md), [`README.md`](./README.md) e READMEs internos (`src/core/README.md`, `src/ports/README.md`, `src/domain/README.md`), corrigindo todos os links relativos quebrados.

---

## [6.6.0] - 2026-11-18 (Hardening Pré-Deploy, Infraestrutura Ubuntu 26.04.1 LTS, Cobertura Pytest 82% e Conformidade SDD - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Corrigido / Hardening Pré-Deploy
- **Proteção Anti-Regressão Temporal no Banco (`src/ports/postgres_repo.py`)**:
  - Aplicado `COALESCE(LEAST(email_status_table.data_pedido, EXCLUDED.data_pedido), EXCLUDED.data_pedido)` em `upsert_from_order` e `COALESCE(LEAST(email_status_table.data_carrinho, EXCLUDED.data_carrinho), EXCLUDED.data_carrinho)` em `upsert_from_cart`, impedindo que atualizações posteriores da Yampi avancem indevidamente a âncora temporal dos cupons.
- **Consistência Temporal UTC-First nos Workers (`src/workers/orders.py` e `src/workers/abandoned_cart.py`)**:
  - `OrderProcessor` passou a incluir `['customer', 'items', 'status', 'shipments', 'transactions']`, utilizar `created_at` como fonte primária de `data_pedido` (com fallback para `transactions[0].created_at` e `updated_at`) e normalizar `row['data_pedido']` retornado do PostgreSQL para UTC timezone-aware.
  - `AbandonedCartProcessor` passou a utilizar `updated_at` com fallback para `created_at` (sem `transactions`), normalizando `row['data_carrinho']` retornado pelo PostgreSQL para UTC timezone-aware.
- **Ciclo de Vida e Fechamento Determinístico de Recursos (`src/ports/smtp_email_provider.py` e `src/main.py`)**:
  - Adicionado método thread-safe `SMTPEmailProvider.close()` (`quit()` com fallback para `close()` e reset de `self._server`).
  - Introduzida função `_close_resources(state_repo, message_provider)` executada em blocos `finally:` nos runners `run_abandoned_carts()`, `run_orders()` e `run_all()`, eliminando vazamento de pools PostgreSQL e conexões SMTP entre ciclos do daemon.
- **Logging Resiliente e Sentry Idempotente (`src/core/logging_config.py`)**:
  - Adicionada flag `_SENTRY_INITIALIZED` garantindo inicialização única e idempotente de `sentry_sdk.init()`.
  - Implementado `SafeRotatingFileHandler`, que cria e valida os diretórios `local_data/logs` e `local_data/emails` e recria pasta/stream automaticamente caso removidos em tempo de execução.

### Adicionado / Modificado (Infraestrutura & Deploy)
- **Infraestrutura de Deploy em Produção (`docker-compose.prod.yml` e `Makefile`)**:
  - Especificação Compose para produção com `postgres:15-alpine` e `message_integration_app`, limites rígidos de recursos (App: 1.50 vCPU / 512 MB; DB: 0.80 vCPU / 512 MB), volume nomeado `message_integration_pgdata`, `no-new-privileges:true` e binding em loopback `127.0.0.1`.
  - Adicionado `mkdir -p containers/logs containers/emails` no alvo `make up` do `Makefile` e atualização do `.gitignore`.
- **Guia de Instalação Ubuntu 26.04.1 LTS & ADR de Deploy (`00_2_GUIA_DE_INSTALACAO_UBUNTU26.md` e `00_DECISOES_DE_PROJETO_DEPLOY.md`)**:
  - Manual completo de implantação local 24/7 no Ubuntu 26.04.1 LTS (`resolute`) com Docker Engine CE (DEB822), systemd sem suspensão, firewall UFW e validação via Sentry Crons (`yampi-daemon-cycle`).
- **Estudos de Entregabilidade & CI/CD**:
  - Adicionados `01_EMAIL_DELIVERABILITY_KEY_POINTS.md`, `02_EMAIL_CERTIFICATION_GUIDE.md`, `project_decisions/10_automationCICD.md` e `project_decisions/antigos/11_version_control_assistant.md`.

### Testes e Qualidade
- **Expansão da Suíte Pytest (`56 passed`, cobertura de `82%` em `src/`)**:
  - Adicionadas novas suítes `tests/test_logging_config.py`, `tests/test_smtp_email_provider.py` e `tests/test_main_and_daemon.py`.
  - Ampliados os testes de regressão temporal, fallback de datas, normalização UTC, `COALESCE(LEAST(...))` e rollback fail-safe em `tests/test_orders.py`, `tests/test_abandoned_cart.py` e `tests/test_postgres_repo_pool.py`.

### Documentação e Conformidade SDD (Zero Doc-Drift)
- Criada especificação canônica [`docs/sdd_specs.md`](./docs/sdd_specs.md) no padrão EARS + cenários `GIVEN / WHEN / THEN` + ADRs leves cobrindo todos os módulos de `src/`.
- Sincronizados [`docs/email_state_machine.md`](./docs/email_state_machine.md), diagramas Mermaid (`docs/diagramas/`), [`docs/architecture.md`](./docs/architecture.md), [`docs/project_overview.md`](./docs/project_overview.md), [`docs/sentry_dashboard_guide.md`](./docs/sentry_dashboard_guide.md), [`docs/project_dependency_tree.md`](./docs/project_dependency_tree.md), [`docs/testing_guidelines.md`](./docs/testing_guidelines.md), [`docs/docker_cheatsheet.md`](./docs/docker_cheatsheet.md), [`docs/README.md`](./docs/README.md), [`scripts/README.md`](./scripts/README.md) e READMEs internos (`src/domain/`, `src/core/`, `src/ports/`, `src/workers/`).
- Sanitizados todos os links Markdown para caminhos relativos portáveis (remoção integral de URIs `file://` e caminhos absolutos `/home/...`) e mascaramento de PII de exemplos conforme LGPD.
- Removido arquivo redundante `RELEASE_NOTES.md`.

---

## [6.5.2] - 2026-08-17 (Governança de Agentes Nativos, Indexação Vetorial Qdrant e Refinamento Arquitetural - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**


### Adicionado / Modificado
- **Migração para Ecossistema Nativo de Agentes (`.agents/`)**:
  - Consolidação e migração de mais de 100 skills e subagentes especializados para a pasta nativa `.agents/skills/`.
  - Centralização e padronização das diretrizes comportamentais e regras de desenvolvimento em `.agents/AGENTS.md` e `.agents/rules/`.
  - Remoção de dependências de referências externas, garantindo isolamento e portabilidade total do repositório.
- **Indexação Vetorial Semântica via Qdrant (`.agents/local_index/`)**:
  - Implementação da infraestrutura de indexação vetorial com Qdrant para busca semântica de regras, skills e documentação do projeto.
- **Orquestração Operacional com Makefile (`Makefile`)**:
  - Implementação de interface Facade com menu auto-documentado (`make help`).
  - Alvos centralizados para controle de containers Docker (`make up`, `make down`, `make logs`, `make sh`).
  - Alvos dedicados para disparo de workers (`make run-all`, `make run-orders`, `make run-carts`) e consultas de banco de dados (`make db-query`, `make db-find`, `make db-del`).
- **Conclusão da Documentação Modular & Padronização de Links**:
  - Finalização do mapeamento de arquitetura em `docs/architecture.md` e árvore de dependências.
  - Correção e padronização rigorosa de links relativos portáveis em toda a pasta `project_decisions/` e `docs/`.
  - Sincronização definitiva do histórico de releases no `CHANGELOG.md`.

---

## [6.5.0] - 2026-08-10 (Orquestração Operacional com Makefile Auto-Documentado - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Interface Centralizada de Operações (`Makefile`)**:
  - Implementado `Makefile` auto-documentado (`make help`) utilizando `awk` para categorização de comandos em tempo real.
  - Alvos dedicados para infraestrutura Docker (`build`, `up`, `down`, `logs`, `restart`, `sh`).
  - Alvos dedicados para execução de workers (`run-all`, `run-orders`, `run-carts`).
  - Alvos de consulta e manutenção de banco de dados (`db-query`, `db-find`, `db-del`, `db-search-orders`, `db-search-carts`).
- **Automação de Build com Tags Dinâmicas (`docker-compose.yml`)**:
  - Injeção da variável `${APP_VERSION}` extraída diretamente do arquivo `VERSION` no tagueamento de imagens.
- **Documentação de Scripts (`scripts/README.md`)**:
  - Mapeamento completo dos scripts shell para a nova interface Facade do Makefile.

---

## [6.4.2] - 2026-08-09 (Arquitetura UTC-First e Proteção Fail-Fast - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Arquitetura de Tempo UTC-First (`src/core/time_utils.py`)**:
  - Implementado `parse_yampi_date_to_utc` forçando a extração estrita de dicionários de data e fuso horário Yampi.
  - Conversão inteligente e padronizada para UTC antes do uso interno na aplicação.
- **Proteção Fail-Fast em Workers (`src/workers/abandoned_cart.py` e `src/workers/orders.py`)**:
  - Incorporado bloco `try/except ValueError` isolando falhas de parsing de datas.
  - Aborto controlado por mensagem e graceful degradation mantendo a resiliência do pool de Threads.
- **Universalização de Logs (`src/core/logging_config.py`)**:
  - Padronização global dos timestamps de Log para UTC, garantindo pareamento um-pra-um com registros de Banco de Dados.
- **Cobertura Pytest e Guias (`docs/` & `tests/`)**:
  - Adição de regra formal para testes obrigatórios de fluxos `try/except` no `docs/testing_guidelines.md` (item 4.4).
  - Atualização de Mocks de integração para compliance com timezone restrito.
  - Criação da suíte `test_time_utils.py` com 100% de cobertura nos caminhos de sucesso e falha via `pytest.raises`.
  - Documentação da arquitetura inserida e consolidada no `docs/architecture.md`.

---

## [6.4.1] - 2026-08-08 (Transações APM de Workers, Guia do Dashboard Sentry e Telemetria em Nuvem - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Transações e Tracing em Workers (`src/workers/abandoned_cart.py` e `src/workers/orders.py`)**:
  - Encapsulamento dos loops de processamento em transações atômicas de APM (`sentry_sdk.start_transaction(op="worker.process", ...)`) garantindo medição precisa de ponta a ponta dos ciclos de execução.
  - Extração e enriquecimento de dados de contexto e breadcrumbs para depuração instantânea no painel do Sentry.
- **Configuração e Variáveis de Telemetria (`.env.example` e `src/core/logging_config.py`)**:
  - Adição de suporte a taxas dinâmicas de amostragem (`TRACES_SAMPLE_RATE`, `PROFILES_SAMPLE_RATE`) e identificação de ambiente (`SENTRY_ENVIRONMENT`).
  - Suporte a profiling de performance contínua em ambientes de produção.
- **Guia do Usuário e Operação do Sentry Dashboard (`docs/sentry_dashboard_guide.md`)**:
  - Criação do manual visual e operacional completo do Sentry cobrindo Issues, Agrupamento, Breadcrumbs, Transações, Spans em Cascata, Monitoramento de Heartbeat (Crons) e Alertas.
- **Documentação de Decisões e Estudos (`project_decisions/`)**:
  - Inclusão do guia prático de observabilidade [`08_sentry_aulas_praticas.md`](./project_decisions/antigos/08_sentry_aulas_praticas.md);
  - Estudo de arquitetura para persistência e agentes de memória temporal [`graphiti_implementation.md`](./project_decisions/estudo/graphiti_implementation.md);
  - Atualização do índice consolidado no `project_decisions/README.md`.

---

## [6.4.0] - 2026-08-07 (Pool de Conexões Postgres, Sentry APM, Rotação de Logs e Governança de Macros - STABLE)


### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Pool de Conexões e Concorrência de Banco (`src/ports/postgres_repo.py`)**:
  - Implementação de `ThreadedConnectionPool` configurável (1 a 20 conexões) para contenção de concorrência e eliminação de vazamento de sockets TCP.
  - Adição do context manager `_get_connection()` garantindo devolução automática (`pool.putconn()`) via blocos `try/finally` e método `close()` para finalização limpa.
- **Observabilidade Completa e APM Sentry (`src/core/client.py`, `src/ports/postgres_repo.py`, `src/daemon.py`, `src/webhook_server.py` e `src/workers/`)**:
  - Instrumentação de Spans de APM manuais (`sentry_sdk.start_span`) em chamadas HTTP da Yampi e consultas SQL no PostgreSQL.
  - Fingerprinting customizado para isolamento de erros de rede (`yampi-rate-limit-429`, `yampi-upstream-downtime-5xx` e `yampi-client-error-4xx`).
  - Monitoramento de Daemons via `sentry_sdk.crons.monitor` com heartbeat configurado para o slug `yampi-daemon-cycle`.
  - Integração do Flask com `FlaskIntegration()` no `src/webhook_server.py` para medição de latência e erros 5xx em tempo real.
  - Emissão de breadcrumbs de negócio (`cart_state_machine` e `order_state_machine`) a cada transição de status `STC` e `STG`.
  - Unificação de captura de exceções globais (processo e threads) diretamente via `sentry_sdk.capture_exception()`.
- **Rotação de Logs e Proteção de I/O em Disco (`src/core/logging_config.py` & `src/core/macros.py`)**:
  - Substituição do `FileHandler` estático por `RotatingFileHandler` com rotação de 200 MB por arquivo (`MACRO_LOG_MAX_BYTES`) e retenção de até 10 backups (`MACRO_LOG_BACKUP_COUNT`), evitando esgotamento de disco em produção.
- **Governança de Macros e Erradicação de Magic Numbers (`src/core/macros.py`)**:
  - Centralização de todas as constantes e literais de Sentry, Postgres, SMTP, Webhooks e Yampi em um único arquivo de referência (`src/core/macros.py`).
  - Implementação de mascaramento dinâmico de e-mails (`_mask_email()`) no `SMTPEmailProvider` respeitando `MACRO_EMAIL_MASK_VISIBLE_PREFIX_CHARS`.
- **Ferramental Operacional e CLI (`scripts/`)**:
  - `scripts/find_by_id.sh`: consulta rápida e flexível por qualquer campo/coluna do banco de dados (ex: sku, order_id, cpf) com exibição formatada.
  - `scripts/delete_by_id.sh`: utilitário interativo de exclusão segura com preview em tabela e confirmações de proteção.
- **Padronização de Testes com Pytest (`requirements.txt` & `docs/testing_guidelines.md`)**:
  - Inclusão das dependências `pytest`, `pytest-mock` e `pytest-cov` no `requirements.txt`.
  - Criação do manual oficial de testes com TDD, injeção de fixtures e parametrização em `docs/testing_guidelines.md`.
- **Documentação e Guias de Arquitetura (`docs/` & `project_decisions/`)**:
  - Guia completo de Git Flow, branches `feature/*`/`hotfix/*` e ciclo de PRs em `docs/project_overview.md`.
  - Elaboração do estudo técnico de observabilidade em `project_decisions/antigos/08_sentry_architecture_and_potential.md`.

---

## [6.3.2] - 2026-08-03 (Resiliência do Provedor SMTP e Tolerância a Falhas na Fase 3 - STABLE)


### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Throttling e Pooling de Conexões SMTP (`src/ports/smtp_email_provider.py`)**:
  - Implementada manutenção de conexão única (Connection Pooling) para evitar desconexões bruscas (Timeouts) do provedor SMTP por excesso de requests concorrentes.
  - Adicionado `threading.Lock()` e delay estratégico de 2.0s entre disparos, contendo o fluxo de multithreading num funil controlado (Rate Limit).
  - Integrado mecanismo de Retry com **Exponential Backoff** (3 tentativas: 5s, 10s, 15s) no handshake e disparo SMTP.
- **Prevenção de Transições Fantasmas na Máquina de Estados (`src/workers/abandoned_cart.py` e `src/workers/orders.py`)**:
  - O banco de dados (SQLite) **não será mais atualizado (Fase 3)** se o SMTP Provider reportar falha de entrega (retornando `False`). Isso garante que os carrinhos e pedidos não transicionem seus status (STG/STC) sem o real disparo da comunicação.
  - Com essa barreira, o cronjob nativo da aplicação efetuará o **retry orgânico** processando as filas ignoradas na próxima rodada, assegurando que nenhum cliente fique sem receber o incentivo de compra.
- **Autodocumentação (`docs/`, `src/`)**:
  - Nova política de resiliência e rate limit documentada através de novos sumários técnicos em todos os diretórios internos.

---

## [6.3.1] - 2026-08-02 (Hardening de Segurança e Resiliência de Payload do Cliente - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Hardening de Extração de Dados do Cliente (`src/workers/orders.py` & `src/workers/abandoned_cart.py`)**:
  - Implementado helper de extração defensiva `_extract_customer_data()` imune a objetos `null`, dicionários planos ou envelopados em `{"data": ...}`, eliminando riscos de `AttributeError` em cadastros de clientes da Yampi.
  - Higienização e sanitização de strings de e-mail com `.strip()` para evitar erros de sintaxe SMTP.
- **Auditoria de Segurança para Produção (`src/core/macros.py` & `src/services/notification_service.py`)**:
  - Validação profunda do fluxo com `MACRO_FORCE_TEST_EMAIL_RECIPIENT = False` garantindo a entrega segura para clientes reais e espelhamento por duplicata (`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = True`).
- **Suíte de Testes de Extração (`tests/test_customer_extraction.py`)**:
  - Adicionada bateria de 4 testes unitários cobrindo variações de payload e prevenindo regressões de runtime.

---

## [6.3.0] - 2026-08-02 (Suporte a Retentativas de Conexão HTTP & Envio de E-mails em Duplicata - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Resiliência e Retentativas HTTP (`src/core/client.py`)**:
  - Implementado sistema de até 3 tentativas (retries) com backoff exponencial (2s, 4s...) na classe `YampiClient.request` para falhas transitórias de conexão (`ConnectionResetError`, `Timeout`, `ChunkedEncodingError`) e erros HTTP 5xx na API da Yampi.
  - Erros 4xx não transitórios (ex: 401, 404) continuam lançando exceção imediatamente sem retentativas desnecessárias.
- **Envio de E-mail em Duplicata para Supervisão (`src/services/notification_service.py` & `src/core/macros.py`)**:
  - Criada a nova macro `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH` que permite enviar simultaneamente uma cópia idêntica de cada e-mail disparado para um cliente real em produção para o e-mail de supervisão (`TEST_EMAIL_RECIPIENT`).
- **Resiliência do Runner de Debug (`src/debug_main.py`)**:
  - Atualizado `debug_main.py` para respeitar dinamicamente a macro `MACRO_ENABLE_REAL_EMAIL_DISPATCH`, permitindo homologar disparos reais via provedor SMTP diretamente nos testes locais.
- **Documentação Técnica (`docs/README.md`)**:
  - Atualizada a central de documentação com seções explicativas cobrindo o algoritmo de retentativas HTTP e o envio em duplicata para supervisão.

---

## [6.2.2] - 2026-08-01 (Especificação Definitiva de Hardware e Limites Docker - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Limites de Recursos Definitivos (`docker-compose.yml`)**:
  - Definidos limites definitivos e reservas de recursos para garantir estabilidade operacional e previsibilidade de custos em nuvem (Cloud VPS KVM / AWS).
  - **`app` (Aplicação)**: `limits` = 1.50 vCPU / 512 MB RAM | `reservations` = 0.50 vCPU / 256 MB RAM.
  - **`db` (PostgreSQL)**: `limits` = 0.80 vCPU / 512 MB RAM | `reservations` = 0.20 vCPU / 128 MB RAM.
  - Comentários detalhados adicionados no `docker-compose.yml` justificando cada limite com base nos testes empíricos de carga.
- **Módulo de Estudos de Capacidade (`project_decisions/estudos/hardware_specs/`)**:
  - Criado o relatório consolidado [`ESTUDO_CAPACIDADE_HARDWARE.md`](./project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md) registrando a bateria de 4 testes de estresse, simulação KVM 1 e o teste de longa exposição de 1 hora e 35 minutos (95 min).
  - Provado empiricamente a **ausência total de vazamentos de memória (*memory leaks*)** (variação de RAM total do stack de apenas 24 MB ao longo de 95 min).
  - Desenvolvido o script Python de automação [`medir_recursos.py`](./project_decisions/estudos/hardware_specs/medir_recursos.py) para medição contínua e salvamento automático de logs em `logs/`.
- **Documentação de Arquitetura (`docs/architecture.md` e `docs/README.md`)**:
  - Adicionada a seção **"Especificação de Hardware e Dimensionamento (Benchmarking)"** com a justificativa de dimensionamento (Sizing X vCPUs / Y MB RAM) para embasar decisões futuras de nuvem.
  - Links relativos portáveis padronizados conforme as diretivas do `.gemini/auto_documentation_rules.md`.

> [!NOTE]
> ⚠️ **AVISO DE PRODUÇÃO (NÃO OFICIAL PARA ENVIO REAL)**:
> Esta versão é **estável** em termos de arquitetura, estabilidade e gerenciamento de recursos. No entanto, o envio oficial de e-mails para clientes reais via provedor SMTP **ainda não está ativado** (`MACRO_ENABLE_REAL_EMAIL_DISPATCH = False` e `MACRO_FORCE_TEST_EMAIL_RECIPIENT = True` em `src/core/macros.py`).

---

## [6.2.1] - 2026-08-01 (Estabilização da Documentação Técnica Divio & Licença Proprietária - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Centralização da Documentação Técnica (`docs/README.md`)**:
  - Criado o portal de referência técnica [`docs/README.md`](./docs/README.md) estruturado conforme a metodologia Divio (Tutorials, How-to, Reference, Explanation).
  - Documentação detalhada sobre a arquitetura Clean/Hexagonal (`src/core`, `src/domain`, `src/ports`, `src/workers`), o funcionamento da Máquina de Estados (STG / STC), execução da suíte de testes unitários e variáveis de ambiente.
- **Redesign da Landing Page (`README.md`)**:
  - Reformulado o `README.md` raiz para servir como onboarding simplificado de desenvolvedores, com links diretos para a documentação técnica centralizada e instruções de inicialização rápida.
- **Licenciamento Proprietário (`LICENSE`)**:
  - Adicionada a licença comercial proprietária formalizando os termos de direito de uso e royalties para exploração comercial do software.
- **Aprimoramento de Telemetria e Alertas**:
  - Atualizada a matriz de observabilidade em `project_decisions/07_future_implementations.md` sinalizando o suporte concluído do Sentry SDK (`v2.66.1`) e fallback de e-mail de traceback SMTP.

---

## [6.2.0] - 2026-08-01 (Notificação Reativa de Erros e Integração Sentry)

### Adicionado / Modificado
- **Observabilidade e Alertas de Erros (`src/core/logging_config.py`)**:
  - Implementado interceptador de exceções não tratadas (`sys.excepthook` e `threading.excepthook`) acionando thread em background para envio automático de e-mail com relatório de falha e anexo contendo as últimas 50.000 linhas (~10MB) do log `app.log`.
  - Adicionadas configurações dedicadas para servidor SMTP de traceback (`TRACEBACK_SMTP_*` e `TRACEBACK_EMAIL_RECIPIENT`) permitindo isolamento total do servidor SMTP de clientes.
- **Integração Sentry SDK**:
  - Atualizado `sentry-sdk` para `2.66.1` no `requirements.txt` com tratamento de resiliência `ImportError`.
  - Documentação e padronização completa de variáveis no `.env.example`.
- **Organização e Roadmap (`project_decisions/07_future_implementations.md`)**:
  - Oficializada a estabilização da Fase 1 (v1.0.0 / v6.1.x) e movido o roadmap de implementações futuras para `project_decisions/07_future_implementations.md`.

> [!IMPORTANT]
> 🌊 **DIVISOR DE ÁGUAS — Transição para a Fase 2 (Aprimoramento do Sistema)**
> - **Fase 1 (v6.1.x e anteriores)**: Declarada oficial, 100% confiável (*reliable*) e totalmente operacional para recuperação de carrinhos e pedidos Yampi via SMTP/WhatsApp.
> - **Fase 2 (v6.2.0+)**: Início do ciclo de aprimoramentos técnicos, observabilidade avançada, notificações reativas de falha e evolução do produto descritos em `project_decisions/07_future_implementations.md`.

---

## [6.1.2] - 2026-08-01 (Isolamento de Volumes Docker e Mapeamento de Logs)

### Adicionado / Modificado
- **Docker e Infraestrutura (`docker-compose.yml`)**:
  - Ajustado o mapeamento de volumes no `docker-compose.yml` para direcionar a pasta do host `./containers/logs` e `./containers/emails` para `/app/local_data/logs` e `/app/local_data/emails` dentro do container.
  - Garante o isolamento completo entre arquivos de teste locais (`./local_data/`) e arquivos gerados em container (`./containers/`).
- **Configuração de Macros (`src/core/macros.py`)**:
  - Atualizadas macros globais de disparo e avisos de segurança no modo de teste.

## [6.1.1] - 2026-08-01 (Correção do Carregamento Local de Imagens e Mocks de E-mail)

### Corrigido
- **Mocks de E-mail e Builder (`builder.py`)**:
  - Corrigido cálculo de caminho base no `builder.py` para utilizar `current_dir / "assets" / "images"`, eliminando a busca em caminho duplicado `/src/src/...` e resolvendo a injeção do placeholder `Folder Not Found`.
  - Removida restrição de prefixo hardcoded na busca de imagens de body nos e-mails de cupom (15% e 20% OFF), garantindo a detecção automática de imagens com novos nomes (`15_desconto.png.png` e `20_desconto.png.png`).
  - Regerados todos os HTMLs de mock na pasta `src/templates/emails/mocks/` com caminhos de imagem `file:///` locais funcionais.

## [6.1.0] - 2026-07-31 (Correção de CID no Docker)

### Corrigido
- **E-mails sem Imagem**: Corrigido um bug silencioso de _path traversal_ no `SMTPEmailProvider` ao ser rodado dentro do Docker. O algoritmo voltava 3 níveis (resultando em `/` no Linux) em vez de 2 níveis (`/app`), o que impedia a anexação de imagens locais via CID e resultava em e-mails com URLs originais relativas sendo reescritas (quebradas) pelo proxy do Gmail.

## [6.0.0] - 2026-07-31 (Auditoria de Segurança Reliable)

### Adicionado / Modificado
- **AppSec (Segurança da Aplicação)**:
  - Implementado teto máximo (*cap*) de 60 segundos no backoff de Rate Limit (`client.py`).
  - Adicionado timeout explícito `timeout=(5, 15)` nas chamadas HTTP (`requests`).
  - Passado flag `verify=True` forçando verificação estrita de TLS contra ataques MitM.
- **DataSec (Segurança de Dados e PII)**:
  - Adicionado `sentry-sdk` (`v2.0.0`) para atuar como interceptador de erros globais (Data Scrubbing), prevenindo o vazamento de tokens e payloads no traceback salvo em disco (`app.log`).
  - Ofuscação proativa do e-mail de destino no `SMTPEmailProvider` para complacência com LGPD.
