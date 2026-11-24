# Arquitetura e Diretivas Spec-Driven

Este documento descreve a infraestrutura não-monolítica e orientada a especificações (Spec-Driven Development) deste projeto. 
Ele serve como guia principal e mapa mental para agentes de IA e desenvolvedores que trabalham nesta base de código.

## 🚨 Diretiva Crítica de Manutenção (Para Agentes de IA e Desenvolvedores)
> [!CAUTION]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> **SEMPRE QUE UM ARQUIVO FOR MODIFICADO, ADICIONADO OU REMOVIDO NESTE PROJETO:**
> Você **DEVE** atualizar imediatamente o arquivo `README.md` local do respectivo diretório onde a mudança ocorreu. Caso a mudança afete o fluxo geral, você deve atualizar este arquivo `architecture.md`. 
> A consistência e veracidade da documentação é um requisito estrito da nossa arquitetura Spec-Driven. Nunca escreva código sem documentar a mudança nos arquivos de documentação da pasta.

## Estrutura de Diretórios e Fluxo de Dados
O projeto adota uma variação de Clean Architecture / Hexagonal Architecture, dividida de forma que a Regra de Negócio não conheça os detalhes de Banco de Dados ou HTTP.

### Mapeamento Geral da Árvore de Arquivos
```bash
├── .agents/                          # Diretrizes comportamentais de IA, skills e versionamento
│   ├── AGENTS.md                     # Código de conduta, Git em modo leitura, SemVer e SDD
│   └── skills/                       # Skills especializadas (ex.: version_control, code-reviewer)
├── docs/                             # Documentação viva e especificações (SDD)
│   ├── README.md                     # Índice técnico de referência
│   ├── sdd_specs.md                  # Catálogo EARS, cenários GIVEN/WHEN/THEN e ADRs
│   ├── email_deliverability_policies.md # Políticas SDD de entregabilidade, domínios, WebP e DNS/Antispam
│   ├── architecture.md               # Detalhes da arquitetura de especificação e camadas
│   ├── diagramas/                    # Diagramas Mermaid da máquina de estados (STG/STC)
│   │   ├── README.md                 # Índice e guia visual dos diagramas
│   │   ├── stateDiagramAbandonedCarts.md # Diagrama Mermaid do fluxo STC (Carrinhos)
│   │   └── stateDiagramOrders.md     # Diagrama Mermaid do fluxo STG (Pedidos)
│   ├── project_dependency_tree.md    # Árvore visual e conceitual de dependências
│   ├── project_overview.md           # Guia funcional completo e decisões de design
│   ├── email_state_machine.md        # Especificação técnica da Máquina de Estados (STG/STC)
│   ├── sentry_dashboard_guide.md     # Especificação de telemetria e observabilidade Sentry
│   ├── testing_guidelines.md         # Diretrizes oficiais de testes (Pytest + TDD)
│   └── docker_cheatsheet.md          # Guia de rotinas e comandos Docker
├── src/                              # Código-fonte principal
│   ├── core/                         # Infraestrutura interna básica do sistema
│   │   ├── client.py                 # Cliente de integração com a API da Yampi
│   │   ├── config.py                 # Dataclasses de configuração e ambiente
│   │   ├── logging_config.py         # SafeRotatingFileHandler, Sentry idempotente e Exception Hooks
│   │   ├── macros.py                 # Constantes e parâmetros temporais/operacionais
│   │   ├── telemetry.py              # Contadores Sentry, spans SMTP, escopos e sanitização LGPD
│   │   └── time_utils.py             # Utilitários UTC-First e conversão Fail-Fast
│   ├── domain/                       # Camada de contratos estritos e specs
│   │   ├── events.py                 # DTOs de eventos (OrderTransitionEvent, CartTransitionEvent)
│   │   └── interfaces.py             # Protocols e Classes Abstratas do sistema
│   ├── ports/                        # Adaptadores de I/O e serviços externos
│   │   ├── message_provider.py       # Mock Provider de Dry-run
│   │   ├── postgres_repo.py          # Repositório PostgreSQL com Pool e COALESCE(LEAST(...))
│   │   └── smtp_email_provider.py    # Adaptador SMTP Stateful (roteamento dual, RFC 2046/5322/8058, WebP/HTTPS, telemetria e close())
│   ├── services/                     # Lógica de serviços injetáveis
│   │   ├── notification_service.py   # Orquestração de builders, escopos Sentry, duplicata e modo homologação
│   │   └── email_builders/           # Builders MJML/Jinja2 e tabela de itens/frete
│   ├── templates/                    # Templates MJML, assets, brand_data.yml e HTMLs compilados
│   ├── workers/                      # Casos de uso e regras de negócio orquestradas
│   │   ├── abandoned_cart.py         # Worker de recuperação de carrinhos (STC)
│   │   └── orders.py                 # Worker de pedidos, PIX, cupons e rastreio (STG)
│   ├── main.py                       # Orquestrador CLI com fechamento de recursos e flush_telemetry() em finally
│   ├── daemon.py                     # Daemon contínuo (5 min) com Sentry Crons
│   ├── debug_main.py                 # Runner de depuração local com flush_telemetry()
│   └── webhook_server.py             # Servidor Flask para Webhooks da Meta API
├── tests/                            # Suíte Pytest (107 testes, 85% de cobertura em src/)
├── scripts/                          # Scripts shell e Python de operação e consulta SQL
├── project_decisions/                # ADRs históricos e estudos técnicos
├── local_data/                       # Dados locais em runtime (logs/ e emails/)
├── containers/                       # Bind mounts do Docker (logs/ e emails/)
├── .env.example                      # Modelo de exemplo para o .env
├── Dockerfile                        # Receita da imagem do container da aplicação
├── docker-compose.yml                # Orquestrador local (App + Postgres)
├── docker-compose.prod.yml           # Orquestrador de produção (hardening e limites de recursos)
├── Makefile                          # Facade operacional (build, up, down, workers, db-*)
├── VERSION                           # Versão SemVer atual
├── CHANGELOG.md                      # Histórico de releases
├── README.md                         # Visão geral e guia rápido do repositório
└── requirements.txt                  # Dependências Python
```

### 1. [`src/domain/`](../src/domain/README.md) (As Especificações)
O coração da aplicação. Não possui implementações, apenas contratos (`Protocols`, `ABC`) e DTOs de eventos (`OrderTransitionEvent`, `CartTransitionEvent`). Tudo no sistema depende do domínio, mas o domínio não depende de nada. Se você vai criar uma funcionalidade nova, **comece especificando-a aqui** e em [docs/sdd_specs.md](./sdd_specs.md).

### 2. [`src/core/`](../src/core/README.md) (Infraestrutura Base e Clientes Internos)
Fornece os blocos de construção internos da nossa infraestrutura:
- Conexão, paginação, backoff e spans APM com a API Yampi (`client.py`)
- Gerenciamento de credenciais via variáveis de ambiente e leitura de `VERSION` (`config.py`)
- Parâmetros centralizados de negócio, SMTP, pool e telemetria (`macros.py`)
- Utilitários **UTC-First** com rejeição *Fail-Fast* de datas *naive* (`time_utils.py`)
- Configuração do Logger central em UTC com `SafeRotatingFileHandler` (recriação automática de diretório/arquivo), inicialização **idempotente** do Sentry (`_SENTRY_INITIALIZED`) e interceptação global de exceções (`logging_config.py`)
- Telemetria e observabilidade de disparos no Sentry (`telemetry.py`): Application Metrics (`email.dispatch.started`, `sent`, `failed`), spans `email.smtp.send`, escopo thread-safe `email_dispatch_scope()`, captura de exceção com *traceback* completo, sanitização LGPD de `frame["vars"]` e `flush_telemetry()`

### 3. [`src/ports/`](../src/ports/README.md) (Adaptadores Externos)
Onde as implementações de terceiros vivem, implementando os contratos do `domain`:
- Provedores de envio de e-mail: `DryRunMessageProvider` (`message_provider.py`) e `SMTPEmailProvider` (`smtp_email_provider.py`, stateful com roteamento dual `transactional@` vs `promotions@`, `threading.Lock`, backoff, `EmailMessage` com `text/plain` + `text/html`, cabeçalhos RFC 5322/8058, suporte a WebP otimizado inline ou HTTPS externo, contadores Sentry + validação de `refused`, mascaramento LGPD e encerramento seguro via `close()`).
- Persistência relacional: `PostgresStateRepository` (`postgres_repo.py`) com `ThreadedConnectionPool`, `FOR UPDATE`, proteção anti-regressão temporal `COALESCE(LEAST(...))` e `close()`.

### 4. [`src/workers/`](../src/workers/README.md) (Regras de Negócio e Use Cases)
Os sub-programas que executam as atividades (Recuperação de Carrinho Abandonado e Atualização de Pedidos). Os workers são isolados, não instanciam conexões e recebem todas as dependências injetadas no construtor pelo Orquestrador.
> **NOTA:** A lógica de estado (STG e STC) processada pelos workers é estritamente regida pela **[Lógica e Máquina de Estados de E-mails](./email_state_machine.md)** e pelos contratos EARS em **[docs/sdd_specs.md](./sdd_specs.md)**.

### 5. `src/main.py` e `src/daemon.py` (Orquestradores / Pontos de Entrada)
`src/main.py` monta as dependências via `get_dependencies()`, injeta-as nos workers e garante a liberação do pool PostgreSQL, o fechamento da conexão SMTP e o envio dos buffers de telemetria (`flush_telemetry()`) em bloco `finally` via `_close_resources()`. `src/daemon.py` executa `run_all()` continuamente a cada `MACRO_DAEMON_SLEEP_INTERVAL_SEG` (`300s`) monitorado pelo Sentry Crons (`yampi-daemon-cycle`).

### 6. `src/webhook_server.py` (Servidor de Webhooks)
Servidor Flask independente que escuta na porta 5000 para receber validações de token (GET) e payloads de mensagens/status em tempo real (POST) vindos da Meta API.

---

## 🌍 Arquitetura UTC-First

### Visão Geral
Toda a aplicação `message_integration` foi projetada utilizando a arquitetura **UTC-First**. 
Isso significa que todo o fluxo de dados, do momento em que entra na nossa fronteira de rede até a gravação no banco de dados, e até mesmo a exportação de Logs, opera **estritamente em Tempo Universal Coordenado (UTC)**.

### Diretrizes de Implementação

#### 1. Rejeição de Datas "Ingênuas" (Fail-Fast)
Não aceitamos datas em formato String plano, pois elas são *naive* (ingênuas, sem fuso horário).
Se a API externa (Yampi) enviar uma data, ela deve fazê-lo num dicionário contendo explicitamente o `timezone`.
```json
// PAYLOAD ACEITO:
"created_at": {
  "date": "2026-08-09 21:37:38.000000",
  "timezone": "America/Sao_Paulo"
}
```
Caso contrário, o utilitário estrito `parse_yampi_date_to_utc` levantará um `ValueError` e a entidade (Pedido ou Carrinho) será descartada do processamento atual e alertada no Sentry. Isso evita que assumamos o fuso incorreto se a API mudar.

#### 2. Banco de Dados e Workers
- Todos os *Timers* de negócio (ex: "Carrinho Abandonado há 1 hora") subtraem `get_now_utc()` da data convertida. A matemática é imune a Horário de Verão (DST).
- O banco PostgreSQL armazena apenas dados em UTC.

#### 3. Logs de Aplicação
Os logs também são gravados em UTC. Isso evita a clássica dor de cabeça de cruzar um horário de erro no banco (que está em UTC) com um log em um fuso horário diferente. A padronização universal se aplica de ponta a ponta.

---

## 💻 Especificação de Hardware e Dimensionamento (Benchmarking)

O sistema passou por baterias empíricas de testes de estresse e longa exposição (1h 35min contínuos), documentadas em [`project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md`](../project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md).

### Requisitos Empíricos do Sistema
* **Memória RAM Total do Stack:** ~177 MiB de pico máximo (ausência completa de *memory leaks* após 95 minutos de execução contínua).
* **Processamento CPU Total do Stack:** ~1.72 vCPUs de pico máximo sob alta carga paralela.

### Limites Definitivos no `docker-compose.yml`
* **`app` (Aplicação):**
  * `limits`: CPU: `1.50 vCPU` | RAM: `512 MB`
  * `reservations`: CPU: `0.50 vCPU` | RAM: `256 MB`
* **`db` (PostgreSQL):**
  * `limits`: CPU: `0.80 vCPU` | RAM: `512 MB`
  * `reservations`: CPU: `0.20 vCPU` | RAM: `128 MB`

### Justificativa de Escolha de Infraestrutura (Sizing)
* **Por que X vCPUs (2.30 vCPUs total estipulado no Docker Compose)?** Garante que o pico de 1.72 vCPUs da aplicação e banco de dados seja processado sem nenhum estrangulamento de CPU (*throttling*).
* **Por que Y MB RAM (512 MB por contêiner / 1 GB total)?** Oferece uma margem de segurança de **3x sobre o consumo de pico real (~177 MB)**, prevenindo completamente qualquer risco de *Out of Memory Kill (OOMKill)*.
* **Armazenamento em Disco para Logs:** O consumo de disco para telemetria é rigorosamente limitado pelo mecanismo de rotação de arquivos (ex: estrutura de 5 logs de 200 MB = 1 GB total). A métrica de retenção é de **3,29 dias/GB** em modo DEBUG e **1.458,21 dias/GB** em modo INFO. Consulte a tabela detalhada em [Logs e Depuração no Project Overview](./project_overview.md#dimensionamento-retenção-e-capacidade-de-armazenamento-de-logs).
* **Provedor de Nuvem Recomendado:**
  * **Cloud VPS KVM 2** (2 vCPUs / 8 GB RAM) — R$ 42,99/mês (ou KVM 1 para MVP de custo reduzido por R$ 29,99/mês).
  * **AWS EC2 `t3.medium`** (2 vCPUs / 4 GB RAM) ou **AWS ECS Fargate (2 vCPU / 4 GB RAM)**.


