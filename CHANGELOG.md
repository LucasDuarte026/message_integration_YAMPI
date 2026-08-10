# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

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
  - Implementada manutenção de conexão única (Connection Pooling) para evitar desconexões bruscas (Timeouts) do provedor Hostinger por excesso de requests concorrentes.
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
  - Atualizado `debug_main.py` para respeitar dinamicamente a macro `MACRO_ENABLE_REAL_EMAIL_DISPATCH`, permitindo homologar disparos reais via SMTP Hostinger diretamente nos testes locais.
- **Documentação Técnica (`docs/README.md`)**:
  - Atualizada a central de documentação com seções explicativas cobrindo o algoritmo de retentativas HTTP e o envio em duplicata para supervisão.

---

## [6.2.2] - 2026-08-01 (Especificação Definitiva de Hardware e Limites Docker - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Limites de Recursos Definitivos (`docker-compose.yml`)**:
  - Definidos limites definitivos e reservas de recursos para garantir estabilidade operacional e previsibilidade de custos em nuvem (Hostinger KVM / AWS).
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
> Esta versão é **estável** em termos de arquitetura, estabilidade e gerenciamento de recursos. No entanto, o envio oficial de e-mails para clientes reais via servidor Hostinger SMTP **ainda não está ativado** (`MACRO_ENABLE_REAL_EMAIL_DISPATCH = False` e `MACRO_FORCE_TEST_EMAIL_RECIPIENT = True` em `src/core/macros.py`).

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
