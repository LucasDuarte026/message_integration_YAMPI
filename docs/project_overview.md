# Comprehensive Project Guide: Message Integration

## 1. Visão Geral (Overview)
Este projeto é um sistema de integração de mensagens projetado para atuar no ecossistema de e-commerce (especialmente integrado à plataforma Yampi). O objetivo primário é fornecer funcionalidades de reengajamento com clientes e comunicação de atualizações vitais, tais como recuperação de carrinhos abandonados e atualizações de status de pedidos.

O sistema foi concebido utilizando metodologias ágeis sólidas:
- **Spec-driven development (SDD)**: Onde as interfaces e contratos são definidos antes das implementações.
- **Test-driven development (TDD)**: Onde testes no padrão **Pytest** orientam a lógica do sistema (detalhado em [Diretrizes de Testes](./testing_guidelines.md)).

Este documento serve como o "Manual do Usuário" e o "Manual do Desenvolvedor" consolidado, fornecendo uma visão ampla, não-técnica e técnica detalhada do projeto de ponta a ponta.

---

## 2. Casos de Uso (Use Cases)

### 2.1 Recuperação de Carrinho Abandonado (Abandoned Cart - Fluxo STC)
- **Problema:** Clientes adicionam produtos ao carrinho, mas saem antes de finalizar a compra.
- **Ação do Sistema:** O sistema consulta a API da Yampi regularmente buscando por carrinhos recém-abandonados (baseando-se em uma janela de horas específica). 
- **Verificação de Estado (STC):** Consulta o banco de dados unificado (`email_status_table`) verificando a coluna `stc` (Status Carrinho). Se `order_id` não for nulo (ou seja, já virou pedido), pula (consulte o [Diagrama de Estados do Carrinho - STC](./diagramas/stateDiagramAbandonedCarts.md)).
- **Execução:** Caso o `stc` permita (ex: transição null→15, 15→16, 16→17), despacha uma mensagem (via provedor SMTP/WhatsApp) contendo o cupom correspondente e o link `simulate_url` para incentivar o retorno à loja, avançando o estado da coluna `stc`.

### 2.2 Atualização de Pedidos (Orders Update - Fluxo STG)
- **Problema:** Clientes precisam estar informados do status de envio, ou serem incentivados a pagar (PIX/Boleto pendente), ou receber cupons de recuperação (pedido travado).
- **Ação do Sistema:** O sistema consulta pedidos recentes na API e avalia contra o estado local.
- **Verificação de Estado (STG):** Consulta a coluna `stg` (Status Global). Verifica a diferença de tempo (`diff`) desde a `data_pedido` ou status da Yampi (consulte o [Diagrama de Estados de Pedidos - STG](./diagramas/stateDiagramOrders.md)).
- **Execução:** Dispara emails correspondentes à transição (ex: Email 1 para pagamento aprovado, Email 2 para incentivo ao PIX, ou Cupons 1, 2, 3 para pedidos não pagos após 24h, 48h, 72h) e avança a máquina de estados `stg`. Evita disparos nos estados terminais definidos pela [Lógica de E-mails](./email_state_machine.md) e visualizados no [Índice de Diagramas](./diagramas/README.md).

---

## 3. Arquitetura e Fluxo (Lógica Sequencial)
A aplicação segue os princípios da **Clean Architecture** e **Hexagonal Architecture**. A regra de negócio principal nunca toca diretamente no banco de dados ou em bibliotecas de rede; ela interage com portas e adaptadores.

### A Lógica de Execução Sequencial
1. **Ponto de Entrada (Entrypoint):** 
   A aplicação é acionada através do `main.py` (para rotinas cron/agendadas) ou via `webhook_server.py` (para eventos em tempo real da Meta/Yampi).
   
2. **Injeção de Dependências:**
   No ponto de entrada (`src/main.py`), as credenciais são lidas (`src/core/config.py`). As conexões são estabelecidas (`src/core/client.py` para Yampi e `src/ports/postgres_repo.py` para PostgreSQL). Os provedores de envio são instanciados (`src/ports/smtp_email_provider.py` ou `src/ports/message_provider.py` em Dry-Run).

3. **Invocação dos Workers:**
   Todas as ferramentas instanciadas no passo anterior são injetadas num *Worker* de caso de uso (ex: `workers/abandoned_cart.py`).

4. **Processamento (Worker):**
   - **Consulta:** O Worker usa a interface injetada do cliente Yampi para pegar os dados puros.
   - **Lógica de Negócio:** Aplica filtros (tempo de abandono, tags, etc).
   - **Estado:** Verifica no Repositório de Estado se o evento já foi processado.
   - **Ação:** Chama o Provedor de Mensagem para enviar o texto.
   - **Confirmação:** Marca no Repositório de Estado que a tarefa foi concluída com sucesso para evitar disparos duplicados.

---

## 4. Quem Executa e Onde Consulta
- **Quem Executa (Regras de Negócio):** O diretório `src/workers/` possui os orquestradores (`AbandonedCartProcessor` e `OrderProcessor`). Eles são o "cérebro" das tarefas individuais, operando de forma concorrente via *ThreadPoolExecutor* para alta vazão.
- **Onde Consulta (Fonte de Dados):**
  - **Externa:** API da Yampi consumida via `src/core/client.py`.
  - **Interna (Estado):** Banco de Dados PostgreSQL unificado (`email_status_table` contendo `cart_id`, `order_id`, `order_number`, `stg`, `stc`, `data_pedido`, `data_carrinho`, `cpf`, `sku`) com suporte a travas de concorrência (`FOR UPDATE`), consultado via `src/ports/postgres_repo.py` para controle da máquina de estados dupla (STG para Pedidos e STC para Carrinhos).
- **O Que Fornece (Saída/Output):** 
  - Comunicações enviadas via provedores de mensagens implementados em `src/ports/` (`SMTPEmailProvider` com SSL/STARTTLS em `smtp_email_provider.py` e `DryRunMessageProvider` em `message_provider.py` para simulações locais).

---

## 5. Decisões de Projeto

- **Infraestrutura Desacoplada:** Ao usar os contratos de `src/domain/interfaces.py`, o projeto pode trocar de provedor de mensagem (SMTP, Meta) alterando apenas a injeção no orquestrador principal sem que o Worker perceba.
- **Tolerância a Falhas e Duplicidade:** O uso estrito do banco de dados relacional atua como uma máquina de estados (STG/STC). As transações garantem que gargalos de API ou execuções paralelas de workers não gerem duplicidade ou *race conditions*.
- **PostgreSQL Connection Pooling (`psycopg2.pool.ThreadedConnectionPool`):** As conexões com o PostgreSQL utilizam um pool thread-safe de 1 a 20 conexões reutilizadas via context managers (`_get_connection()`), prevenindo sobrecarga de conexões TCP e falhas de resolução de DNS interno do Docker em alta concorrência.
- **Controle de Vazão e Resiliência SMTP:** A infraestrutura de envio utiliza *Connection Pooling*, *Throttling* centralizado (travas de `threading.Lock`) e *Exponential Backoff* para evitar banimentos por SPAM nos provedores de e-mail e falhas por *Timeouts*.
- **Roteamento Dual SMTP (`transactional@` vs. `promotions@`) & Entregabilidade RFC 2046/5322/8058:** O [`SMTPEmailProvider`](../src/ports/smtp_email_provider.py) isola envios transacionais (`_server`) e promocionais (`_promo_server` via `PROMO_SMTP_*` com fallback automático), gera alternativa `text/plain` antes do HTML (`BaseEmailBuilder.build_with_plain_text`), injeta `Message-ID`, `Date`, `Reply-To` e `List-Unsubscribe: One-Click` (promocionais), e carrega ativos WebP otimizados de forma modular via `EMAIL_ASSETS_DIR`.
- **Telemetria Sentry Application Metrics & Traceback LGPD (`src/core/telemetry.py`):** Emite contadores de início (`email.dispatch.started`), entrega SMTP confirmada (`email.dispatch.sent`, após validar ausência de `refused` e antes do *throttling*) e falha (`email.dispatch.failed`), correlacionando cada disparo por `trace_id` com *traceback* completo, contexto de negócio e sanitização LGPD em `frame["vars"]`.
- **Auto-documentação Estrita:** Exigência de que regras e contratos guiem o desenvolvimento. 
> [!CAUTION]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação no código-fonte, a documentação (tanto este overview geral quanto os READMEs marginais em `src/`) deve sofrer atualizações imediatas respectivas a essas mudanças para refletir o comportamento real do sistema em produção.

---

## 6. Logs e Depuração

### Fluxo de Logs e Tratamento Global de Erros
O sistema utiliza o módulo de logging nativo do Python configurado globalmente em [logging_config.py](../src/core/logging_config.py) com timestamps padronizados em **UTC**.
- **Destinos da Saída:** Console (`sys.stdout`) e arquivo rotativo resiliente via `SafeRotatingFileHandler` (`local_data/logs/app.log`, que garante e recria automaticamente os diretórios `local_data/logs` e `local_data/emails` mesmo se removidos em runtime).
- **Nível de Logs:** `INFO` por padrão (ou `DEBUG` com `VERBOSE=1`).
- **Inicialização Idempotente do Sentry:** A função `setup_logging()` protege `sentry_sdk.init()` com a flag `_SENTRY_INITIALIZED`, garantindo inicialização única mesmo em múltiplas chamadas.
- **Interceptação Global e Telemetria de Exceções:** O sistema substitui o comportamento padrão do Python instalando `sys.excepthook` e `threading.excepthook`. Qualquer exceção inesperada ou erro fatal é capturado e registrado como `CRITICAL` (`FATAL ERROR`), sendo despachado imediatamente para o **Sentry SDK** (`SENTRY_DSN`) com *Data Scrubbing* ativado (`send_default_pii=False`).
- **Observabilidade Total com Sentry (Fase 2):**
  - **Sentry Crons / Heartbeats (`daemon.py`):** Monitora a saúde do daemon de 5 em 5 minutos (`yampi-daemon-cycle`), emitindo alertas se o ciclo congelar ou for morto silenciosamente.
  - **Flask Integration (`webhook_server.py`):** Coleta latência, throughput e exceções nos webhooks do WhatsApp.
  - **Breadcrumbs de Negócio (`orders.py` e `abandoned_cart.py`):** Grava o histórico de transições de status (`STG` e `STC`) antes de qualquer erro.
  - **APM & Distributed Tracing (`client.py`, `postgres_repo.py` e `smtp_email_provider.py`):** Mede com precisão milimétrica a latência de requisições HTTP da API Yampi (`http.client`), queries de banco de dados (`db.sql.query`) e tentativas SMTP (`email.smtp.send`).
  - **Application Metrics & Captura de Falhas SMTP (`src/core/telemetry.py`):** Contabiliza `email.dispatch.started`, `email.dispatch.sent` e `email.dispatch.failed` via `sentry_sdk.metrics.count` sob escopo thread-safe (`email_dispatch_scope`), captura falhas em `template_build`, `smtp_retries_exhausted` e `smtp_fatal` com *traceback* completo (sem duplicar issues via `DedupeIntegration` e `logger.warning`), sanitiza `frame["vars"]` e realiza `flush_telemetry()` no `_close_resources()` de `main.py` e no fim de `debug_main.py`.
  - **Data Scrubbing (`send_default_pii=False`):** Descarte de dados sensíveis e PII para aderência estrita à LGPD.
- **Rastreamento de Regras:** Os workers registram em `DEBUG`/`INFO` as decisões de precheck, âncoras temporais normalizadas em UTC e transições aplicadas (`[REGRA APLICADA]`).

### Depuração Interativa e Execução Rápida
Para rastrear a execução linha por linha e acompanhar a pilha de chamadas e objetos (incluindo chamadas de funções filhas) de forma visual:
*   **Depurador em IDE (VS Code):** Configurado no arquivo [.vscode/launch.json](../.vscode/launch.json) para que o desenvolvedor possa colocar breakpoints no código e debugar de forma gráfica os comandos `abandoned-carts` e `orders` rodando localmente.
*   **Execução contínua (Daemon):** O orquestrador oficial de execução contínua é o arquivo `src/daemon.py`. Todas as flags de disparo ou modo de simulação devem ser configuradas via código em `src/core/macros.py`.
*   **Mapeamento no Docker:**
Para persistência local e facilidade de depuração no ambiente host, o [docker-compose.yml](../docker-compose.yml) mapeia a pasta local `./local_data/logs` para `/app/local_data/logs` dentro do container da aplicação. Isso permite visualizar a execução em tempo real rodando comandos como `tail -f local_data/logs/app.log`.

### Dimensionamento, Retenção e Capacidade de Armazenamento de Logs

Para assegurar previsibilidade no consumo de armazenamento e evitar esgotamento de disco (*Disk Full*), o sistema emprega o `SafeRotatingFileHandler` (subclasse de `RotatingFileHandler`), parametrizado em `src/core/macros.py` através de `MACRO_LOG_MAX_BYTES` (200 MB) e `MACRO_LOG_BACKUP_COUNT` (10 backups; total máximo de ~2,2 GB considerando o arquivo ativo).

#### Memória RAM vs. Armazenamento em Disco
* **Memória RAM:** O consumo é residual e praticamente nulo (~8 KB). Os handlers realizam `flush()` imediato após a emissão de cada registro, não havendo buffers em memória volátil nem risco de vazamento de memória (*memory leaks*) decorrentes de telemetria.
* **Armazenamento em Disco:** Governança baseada em rotação de arquivos de $X\text{ MB}$ cada (1 arquivo ativo `app.log` + backups sequenciais `app.log.1` a `app.log.N`).

#### Tabela de Métricas Empíricas e Retenção (Métrica por GB)

Abaixo estão os resultados consolidados a partir da medição direta dos logs históricos de teste e execução contínua em container:

| Métrica / Parâmetro | Modo DEBUG / Verbose (`-v`) | Modo INFO / Produção (Padrão) |
| :--- | :--- | :--- |
| **Volume Diário de Caracteres** | ~322.688.910 chars/dia (~322,7M) | ~731.521 chars/dia (~731,5k) |
| **Linhas Geradas por Dia** | ~1.787.174 linhas/dia | ~6.813 linhas/dia |
| **Taxa Diária de Dados** | **311,02 MB/dia** (~0,3037 GB/dia) | **0,70 MB/dia** (~0,000686 GB/dia) |
| **Métrica de Retenção / GB** | **3,29 dias por GB** | **1.458,21 dias por GB** (~4 anos/GB) |
| **Retenção: 5 Logs de 200 MB (referência 1 GB)** | **~3,22 dias** (~3 dias e 5 horas) | **~1.428,57 dias** (~3,9 anos) |
| **Fórmula Geral ($N$ logs de $X\text{ MB}$ cada)** | $\text{Dias} = \frac{N \times X\text{ MB}}{311{,}02\text{ MB/dia}}$ | $\text{Dias} = \frac{N \times X\text{ MB}}{0{,}70\text{ MB/dia}}$ |

> [!NOTE]
> Na configuração atual de `src/core/macros.py` (`MACRO_LOG_MAX_BYTES = 200 MB`, `MACRO_LOG_BACKUP_COUNT = 10`), o limite rígido em disco é de até **11 arquivos** (1 ativo `app.log` + 10 backups = ~2,2 GB), proporcionando ~7 dias de rastreabilidade passo a passo em modo DEBUG ou mais de 8 anos em modo INFO.


---

## 7. Configuração Detalhada e Variáveis de Ambiente (`.env`)

O arquivo [config.py](../src/core/config.py) e os módulos de inicialização ([logging_config.py](../src/core/logging_config.py), [main.py](../src/main.py) e [daemon.py](../src/daemon.py)) carregam as variáveis de ambiente abaixo. Consulte [`.env.example`](../.env.example):

| Variável | Descrição | Padrão | Obrigatória? |
| :--- | :--- | :--- | :--- |
| `YAMPI_USER_TOKEN` | Token do usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_USER_SECRET_KEY` | Chave secreta de usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_ALIAS` | Alias da sua loja Yampi (opcional; detectado via `auth/me` se omitido). | `None` | Não |
| `DATABASE_URL` | URI completa de conexão PostgreSQL (injetada no Docker Compose via `DB_*`). | `postgresql://postgres:mysecretpassword@localhost:5432/message_integration` | **Sim (Produção)** |
| `DB_USER` / `DB_PASSWORD` / `DB_NAME` | Credenciais do serviço PostgreSQL no `docker-compose.yml` / `docker-compose.prod.yml`. | - | **Sim (Docker)** |
| `TEST_EMAIL_RECIPIENT` | E-mail de destino para homologação ou cópia de supervisão em duplicata. | Configurável via `.env` | Não |
| `MAX_WORKERS` | Quantidade máxima de threads paralelas para processamento (`<= 1` ativa modo síncrono). | `10` | Não |
| `VERBOSE` | Ativa logs em nível `DEBUG` (`1`, `true`, `yes`). | `0` (`INFO`) | Não |
| **SMTP Configs (Clientes)** | | | |
| `SMTP_USER` | Usuário de autenticação do servidor SMTP principal. | `None` | **Sim (Modo Produção)** |
| `SMTP_PASSWORD` | Senha ou Token de App do e-mail SMTP. | `None` | **Sim (Modo Produção)** |
| `SMTP_HOST` | Host do servidor de e-mail. | `smtp.gmail.com` | Não |
| `SMTP_PORT` | Porta do servidor SMTP (`465` para SSL ou `587` para STARTTLS). | `587` | Não |
| `SMTP_FROM` | E-mail remetente exibido no cabeçalho dos avisos transacionais (`transactional@yourstore.com`). | `SMTP_USER` | Não |
| `PROMO_SMTP_USER` / `PROMO_SMTP_PASSWORD` / `PROMO_SMTP_FROM` | Credenciais opcionais para disparos promocionais (`promotions@yourstore.com`). | `None` (usa principal) | Não |
| `EMAIL_ASSETS_DIR` | Diretório modular das imagens da marca (não versionadas no Git; anexar em `src/templates/emails/assets/images/` e usar `/app/email_assets` no Docker). | `src/templates/emails/assets/images` | Não |
| `EMAIL_FROM_NAME` | Nome amigável exibido no cabeçalho `From`. | `YourBrand` | Não |
| `EMAIL_REPLY_TO` | Endereço de resposta (`Reply-To`) para atendimento. | `"Customer Support" <promotions@yourstore.com>` | Não |
| `EMAIL_MESSAGE_ID_DOMAIN` | Domínio utilizado para gerar o cabeçalho `Message-ID` (RFC 5322). | `yourstore.com` | Não |
| `EMAIL_UNSUBSCRIBE_URL` / `EMAIL_UNSUBSCRIBE_MAILTO` | Endpoints de descadastramento One-Click (RFC 8058) em fluxos promocionais. | `https://yourstore.com/unsubscribe` | Não |
| **Sentry Configs** | | | |
| `SENTRY_DSN` | DSN do projeto no Sentry para monitoramento em nuvem. | `None` | Não |
| `TRACES_SAMPLE_RATE` | Taxa de amostragem de transações APM (`0.0` a `1.0`). | `1.0` | Não |
| `ENVIRONMENT` | Nome do ambiente no Sentry (`production`, `staging`, `development`). | `production` | Não |

---

## 8. Servidor de Webhooks (WhatsApp / Meta API)

Para escutar eventos em tempo real do WhatsApp da Meta Cloud API:

1. **Início do Servidor:**
   ```bash
   python -m src.webhook_server
   ```
2. O servidor roda por padrão na porta `5000` (`MACRO_WEBHOOK_SERVER_PORT`, endpoint `/webhook`).
3. Para expor em homologação local, utilize um túnel HTTP (ex: `ngrok http 5000`).
4. **Token de Verificação GET:** Configurado por `MACRO_META_WEBHOOK_VERIFY_TOKEN` em [`src/core/macros.py`](../src/core/macros.py#L110) e consumido por `VERIFY_TOKEN` em [`src/webhook_server.py`](../src/webhook_server.py#L25).
5. **POST Handlers:** Processa payloads JSON enviados pela Meta com atualizações de entrega e status de leitura das mensagens.

---

## 9. Política de Versionamento e Roadmap (Semantic Versioning 2.0.0)

Este projeto adota estritamente o padrão **[Semantic Versioning (SemVer 2.0.0)](https://semver.org/lang/pt-BR/)** no formato `MAJOR.MINOR.PATCH`:

- **MAJOR (`X.0.0`) — Mudanças Estruturais / Breaking Changes**: Incompatibilidades no esquema do banco (`email_status_table`), refatorações centrais na arquitetura do daemon ou alteração nos contratos das interfaces de domínio.
- **MINOR (`1.X.0`) — Novas Funcionalidades (Retrocompatíveis)**: Novos provedores de mensagens, novas regras de transição/cupons, melhorias de infraestrutura ou utilitários CLI.
- **PATCH (`1.0.X`) — Bug Fixes e Ajustes Finos**: Correções de erros pontuais, ajustes de tratamento de logs ou refinamento em formatadores sem alteração de regras de negócio.

Os registros de versão são mantidos no arquivo [VERSION](../VERSION), detalhados no [CHANGELOG.md](../CHANGELOG.md) e marcados no Git através de **Annotated Tags** (ex: `git tag -a v6.2.0 -m "..."`).

---

## 10. Estratégia de Branches e Workflow Git (GitHub Flow)

Este projeto segue estritamente o **GitHub Flow** com Pull Requests obrigatórios para garantir estabilidade, rastreabilidade e isolamento de código.

### 🛡️ Proteção da Branch Principal (`main`)
- **Proibição de Desenvolvimento Direto:** É estritamente proibido criar commits ou desenvolver funcionalidades diretamente na branch `main`.
- **Origem de Produção:** A branch `main` representa o código estável e pronto para implantação. Todas as mudanças entram na `main` exclusivamente através de **Pull Requests (PR)** aprovados no GitHub.

### 🔀 Nomenclatura e Tipos de Branches
Todo novo desenvolvimento deve ser isolado em uma branch criada a partir da `main` utilizando os seguintes prefixos padrão:

1. **`feature/*` ou `features/*` (Funcionalidades e Otimizações Planejadas)**
   - Utilizada para criar novas funcionalidades, adicionar novos provedores, atualizar templates, criar testes ou refatorar módulos.
   - **Exemplos:** `feature/newman-tests`, `feature/smtp-connection-pooling`, `feature/fastapi-webhook`.

2. **`hotfix/*` (Correções Emergenciais de Produção)**
   - Utilizada exclusivamente para corrigir bugs críticos e imediatos encontrados em ambiente de teste/produção.
   - **Exemplos:** `hotfix/fix-pix-link-formatting`, `hotfix/db-lock-timeout`, `hotfix/image-asset-path`.

### 🔄 Ciclo de Vida de uma Alteração (Do Card ao Merge)

```mermaid
graph LR
    A[main] -->|git checkout -b| B[feature/minha-feature]
    B -->|commits locais| C[Conventional Commits]
    C -->|git push -u origin| D[Branch Remota no GitHub]
    D -->|Abrir PR| E[Pull Request no GitHub]
    E -->|Revisão e Validação| F[Merge PR para main]
    F -->|git checkout main && git pull| G[main local atualizada]
    G -->|Tag de Release se aplicável| H[git tag -a vX.Y.Z]
```

1. **Criação da Branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout -b feature/nome-da-funcionalidade
   # Ou para correções:
   git checkout -b hotfix/descricao-do-bug
   ```

2. **Desenvolvimento com Conventional Commits:**
   Commits devem ser atômicos e seguir a convenção:
   - `feat: ...` ➔ Nova funcionalidade
   - `fix: ...` ➔ Correção de bug
   - `docs: ...` ➔ Alterações em documentação
   - `test: ...` ➔ Adição ou correção de testes
   - `refactor: ...` ➔ Refatoração de código sem alterar regra de negócio
   - `chore: ...` ➔ Tarefas de manutenção ou dependências

3. **Publicação da Branch e Abertura do Pull Request:**
   ```bash
   git push -u origin feature/nome-da-funcionalidade
   ```
   Acesse o repositório no **GitHub** e abra o **Pull Request** direcionado para a branch `main`.

4. **Merge no GitHub e Sincronização Local:**
   Após a aprovação e *Merge* do PR na interface do GitHub:
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/nome-da-funcionalidade
   ```

5. **Release e Versionamento (Quando aplicável):**
   Se o merge contiver um marco/release, estampar a tag SemVer correspondente na `main`:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z: Descrição sumária"
   git push origin main --tags
   ```

---

> [!IMPORTANT]
> 🌊 **DIVISOR DE ÁGUAS — Transição da Fase 1 para a Fase 2**
> - **Fase 1 (v6.1.x e versões anteriores)**: Considerada a versão base oficial, 100% confiável (*reliable*) e totalmente operacional em produção para recuperação de carrinhos e acompanhamento de pedidos.
> - **Fase 2 (v6.2.0+)**: Representa a fase de aprimoramento e otimização contínua do sistema. O planejamento evolutivo segue norteado pelas especificações formais e ADRs em [docs/sdd_specs.md](./sdd_specs.md).
