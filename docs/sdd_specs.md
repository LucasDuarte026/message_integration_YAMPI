# Especificações Formais (SDD — Spec-Driven Development)

**Status:** Ativo / Fonte Canônica de Contratos Comportamentais  
**Versão Alvo:** `6.7.0`  
**Padrão:** EARS (*Easy Approach to Requirements Syntax*) + Cenários Verificáveis (`GIVEN / WHEN / THEN`)  
**Documentos Complementares:** [Arquitetura](./architecture.md) · [Políticas de Entregabilidade (SDD)](./email_deliverability_policies.md) · [Máquina de Estados STG/STC](./email_state_machine.md) · [Telemetria Sentry](./sentry_dashboard_guide.md) · [Diretrizes de Testes](./testing_guidelines.md)

---

## 1. Propósito e Regra de Paridade SDD

Este documento consolida todos os requisitos normativos implementados em `src/`, garantindo **Zero Doc-Drift** entre o código-fonte, a especificação comportamental e a suíte automatizada em `tests/`.

- Toda regra de negócio, invariante de persistência, resiliência de I/O ou política de ciclo de vida implementada no código possui um requisito `REQ-*` correspondente abaixo.
- Todo requisito `REQ-*` referencia diretamente os arquivos de implementação e os respectivos testes em `tests/`.

---

## 2. Catálogo de Requisitos Normativos (EARS)

### `REQ-01` — Arquitetura Temporal UTC-First e Fail-Fast de Datas
- **Módulos:** [`src/core/time_utils.py`](../src/core/time_utils.py)
- **Testes:** [`tests/test_time_utils.py`](../tests/test_time_utils.py), [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. O sistema **DEVE** calcular o instante atual exclusivamente em UTC timezone-aware por meio de `get_now_utc()`.
  2. O sistema **DEVE** exigir payloads de data da Yampi no formato `{"date": "...", "timezone": "..."}` (aceitando `"%Y-%m-%d %H:%M:%S.%f"` com fallback `"%Y-%m-%d %H:%M:%S"`) e rejeitar strings *naive* ou campos ausentes levantando `ValueError` (*Fail-Fast*).
  3. O sistema **DEVE** converter datas com timezone válido (ex.: `America/Sao_Paulo`) para UTC antes de qualquer cálculo ou gravação em banco.
  4. A função `to_local_sp(dt)` **DEVE** ser utilizada apenas para exibição/apresentação, tratando datetimes *naive* recebidos como UTC antes da conversão para `America/Sao_Paulo`.
- **Cenário Verificável:**
  - **DADO** um payload `{"date": "2026-08-09 21:37:38.000000", "timezone": "America/Sao_Paulo"}`
  - **QUANDO** `parse_yampi_date_to_utc` é invocada
  - **ENTÃO** retorna um `datetime` timezone-aware em UTC (`2026-08-10 00:37:38+00:00`).
  - **DADO** um payload string plano, `None`, sem `timezone` ou com timezone inválido
  - **QUANDO** `parse_yampi_date_to_utc` é invocada
  - **ENTÃO** levanta `ValueError` imediatamente.

---

### `REQ-02` — Resiliência HTTP, Descoberta de Alias e Paginação na API Yampi
- **Módulos:** [`src/core/client.py`](../src/core/client.py), [`src/core/macros.py`](../src/core/macros.py)
- **Testes:** [`tests/test_client.py`](../tests/test_client.py), [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. Quando `merchant_alias` não for informado, `YampiClient` **DEVE** consultar `POST auth/me`, priorizar a primeira loja com `active=True` e fazer fallback para a primeira loja da lista se nenhuma estiver ativa.
  2. Em requisições `GET`, o cliente **DEVE** injetar `skipCache=true` por padrão para evitar leitura de cache de 30 minutos da Yampi.
  3. Em respostas HTTP `429`, HTTP `5xx` ou falhas transitórias de rede (`ConnectionError`, `Timeout`, `ChunkedEncodingError`), o cliente **DEVE** realizar até `MACRO_HTTP_MAX_RETRIES` (`3`) tentativas com *backoff* exponencial a partir de `MACRO_HTTP_INITIAL_BACKOFF_SEG` (`2.0s`) limitado a `MACRO_HTTP_MAX_BACKOFF_SEG` (`60.0s`).
  4. Em erros HTTP `4xx` não transitórios (ex.: `401`, `404`), o cliente **DEVE** falhar imediatamente (*Fail-Fast*) sem retentativas.
  5. Cada chamada HTTP **DEVE** ser instrumentada com span Sentry `op="http.client"`.
- **Cenário Verificável:**
  - **DADO** uma resposta `429` seguida de resposta `200` com paginação em 2 páginas
  - **QUANDO** `get_orders()` itera sobre o gerador
  - **ENTÃO** executa backoff após o `429`, retenta a chamada e entrega todos os itens das páginas `1` e `2`.

---

### `REQ-03` — Configuração de Ambiente e Governança de Macros
- **Módulos:** [`src/core/config.py`](../src/core/config.py), [`src/core/macros.py`](../src/core/macros.py), [`VERSION`](../VERSION)
- **Testes:** [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. `load_config()` **DEVE** exigir `YAMPI_USER_TOKEN` e `YAMPI_USER_SECRET_KEY` no ambiente e levantar `ValueError` se qualquer um estiver ausente.
  2. `load_config()` **DEVE** ler `YAMPI_ALIAS`, `DATABASE_URL`, `TEST_EMAIL_RECIPIENT`, `SMTP_HOST` (padrão `"smtp.gmail.com"`), `SMTP_PORT` (inteiro, padrão `587`), `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`, `PROMO_SMTP_USER`, `PROMO_SMTP_PASSWORD`, `PROMO_SMTP_FROM`, `EMAIL_FROM_NAME`, `EMAIL_REPLY_TO`, `EMAIL_MESSAGE_ID_DOMAIN`, `EMAIL_UNSUBSCRIBE_URL`, `EMAIL_UNSUBSCRIBE_MAILTO`, `EMAIL_ASSETS_DIR` (padrão `MACRO_DEFAULT_EMAIL_ASSETS_DIR`), `MAX_WORKERS` (inteiro, padrão `10`) e ler a versão da aplicação a partir do arquivo `VERSION` na raiz do projeto (com fallback para `"unknown"`).
  3. Todas as constantes temporais, flags de envio, parâmetros de pool PostgreSQL, SMTP, identidade de cabeçalhos de e-mail, HTTP e telemetria **DEVEM** ser centralizados em `src/core/macros.py`.
  4. Na configuração padrão atual de `macros.py`, o modo de produção SMTP está ativo com prevenção de *Graymail* (`MACRO_ENABLE_REAL_EMAIL_DISPATCH = True`, `MACRO_FORCE_TEST_EMAIL_RECIPIENT = False`, `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = False`, `MACRO_ENABLE_LOCAL_HTML_SAVING = False`).
- **Cenário Verificável:**
  - **DADO** variáveis `YAMPI_USER_TOKEN` ausentes no ambiente
  - **QUANDO** `load_config()` é chamada
  - **ENTÃO** levanta `ValueError` impedindo inicialização parcial.

---

### `REQ-04` — Logging Seguro em UTC, Diretórios Automáticos e Sentry Idempotente (LGPD)
- **Módulos:** [`src/core/logging_config.py`](../src/core/logging_config.py)
- **Testes:** [`tests/test_logging_config.py`](../tests/test_logging_config.py), [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. `setup_logging()` **DEVE** garantir a criação automática da pasta de logs (`log_file`) e do diretório de e-mails (`emails_dir`, padrão `local_data/emails`).
  2. O handler de arquivo `SafeRotatingFileHandler` **DEVE** verificar e recriar a pasta pai antes de abrir o arquivo e durante `emit()`, reabrindo o stream se o arquivo de log tiver sido removido em tempo de execução.
  3. Quando `SENTRY_DSN` estiver definido, `setup_logging()` **DEVE** inicializar `sentry_sdk.init(...)` de forma **idempotente** controlada por `_SENTRY_INITIALIZED`, com `send_default_pii=False` (conformidade LGPD).
  4. O formatador de logs **DEVE** utilizar exclusivamente timestamps UTC (`get_now_utc().timetuple()`).
  5. Exceções não tratadas na thread principal (`sys.excepthook`) e em threads filhas (`threading.excepthook`), exceto `KeyboardInterrupt`, **DEVEM** ser logadas como `CRITICAL` e enviadas ao Sentry.
- **Cenário Verificável:**
  - **DADO** um `SafeRotatingFileHandler` ativo cuja pasta de logs é removida em runtime
  - **QUANDO** uma nova mensagem é registrada no logger
  - **ENTÃO** a pasta e o arquivo são recriados automaticamente e a mensagem é persistida sem lançar exceção.
  - **DADO** múltiplas invocações de `setup_logging()` com `SENTRY_DSN` definido
  - **QUANDO** `_SENTRY_INITIALIZED` passa a `True` na primeira chamada
  - **ENTÃO** `sentry_sdk.init` é invocado exatamente uma vez.

---

### `REQ-05` — Repositório PostgreSQL, Pool Thread-Safe e Proteção Anti-Regressão Temporal
- **Módulos:** [`src/ports/postgres_repo.py`](../src/ports/postgres_repo.py), [`src/domain/interfaces.py`](../src/domain/interfaces.py)
- **Testes:** [`tests/test_postgres_repo_pool.py`](../tests/test_postgres_repo_pool.py)
- **Requisito (EARS):**
  1. `PostgresStateRepository` **DEVE** gerenciar conexões por meio de `ThreadedConnectionPool` dimensionado entre `MACRO_PG_POOL_MIN_CONN` (`1`) e `MACRO_PG_POOL_MAX_CONN` (`20`) e devolver sempre a conexão via `pool.putconn(conn)` em bloco `finally` de `_get_connection()`.
  2. O método `close()` **DEVE** encerrar todas as conexões do pool via `pool.closeall()`.
  3. Na inicialização (`_init_db`), o repositório **DEVE** criar `email_status_table` e os índices `idx_email_status_cpf`, `idx_email_status_cpf_sku` e `idx_email_status_order_number`, propagando exceções em caso de falha crítica de bootstrap.
  4. Em `upsert_from_order`, novos registros **DEVEM** inserir `data_carrinho = NULL`; em caso de conflito por `cart_id`, `data_carrinho` é preservado e `data_pedido` **DEVE** ser protegido contra regressão/avanço indevido de data usando `COALESCE(LEAST(email_status_table.data_pedido, EXCLUDED.data_pedido), EXCLUDED.data_pedido)`, seguida de `SELECT ... FOR UPDATE` na mesma transação curta.
  5. Em `upsert_from_cart`, novos registros **DEVEM** inserir `order_number = 'N/A'` (`order_id = NULL`, `data_pedido = NULL`); em caso de conflito por `cart_id`, `data_carrinho` **DEVE** ser protegido usando `COALESCE(LEAST(email_status_table.data_carrinho, EXCLUDED.data_carrinho), EXCLUDED.data_carrinho)`, seguida de `SELECT ... FOR UPDATE`.
  6. Campos `NOT NULL` ausentes (`cpf`, `sku`, `order_number`) **DEVEM** receber os fallbacks de `macros.py` (`"00000000000"`, `"N/A"`). Em falhas SQL de `upsert_from_order`/`upsert_from_cart`, o método **DEVE** logar o erro e retornar `None`.
  7. `update_stg` e `update_stc` **DEVEM** gravar `timestamp_ultimo_email` em UTC (`get_now_utc()`) e capturar exceções SQL sem propagar falha fatal para a thread.
- **Cenário Verificável:**
  - **DADO** um registro já existente com `data_pedido = T1` e uma nova atualização com `EXCLUDED.data_pedido = T2 > T1`
  - **QUANDO** `upsert_from_order` executa `ON CONFLICT (cart_id) DO UPDATE`
  - **ENTÃO** `email_status_table.data_pedido` permanece preservado em `T1` (`LEAST(T1, T2)`).

---

### `REQ-06` — Provedor SMTP Stateful (`EmailMessage`, RFC 2046/5322/8058), Throttling, Mascaramento LGPD e `close()`
- **Módulos:** [`src/ports/smtp_email_provider.py`](../src/ports/smtp_email_provider.py), [`src/ports/message_provider.py`](../src/ports/message_provider.py)
- **Testes:** [`tests/test_smtp_email_provider.py`](../tests/test_smtp_email_provider.py), [`tests/test_dual_sender_routing.py`](../tests/test_dual_sender_routing.py)
- **Requisito (EARS):**
  1. `SMTPEmailProvider` **DEVE** reutilizar uma conexão SMTP persistente protegida por `threading.Lock` (validando a conexão ativa via `noop()[0] == 250` antes de reutilizá-la), utilizando `SMTP_SSL` na porta `465` e `SMTP` + `STARTTLS` nas demais portas, autenticando com `login()` quando `user` e `password` estiverem definidos, e resolvendo `from_addr` via `from_addr or user or MACRO_DEFAULT_FALLBACK_FROM_EMAIL`.
  2. O provedor **DEVE** construir a mensagem via `email.message.EmailMessage`, injetando `Message-ID` único (`make_msgid(domain=self.message_id_domain)`), `Date` (`formatdate(localtime=True)`), `From` formatado com nome amigável (`formataddr`) e `Reply-To`, além de `List-Unsubscribe` e `List-Unsubscribe-Post: List-Unsubscribe=One-Click` exclusivamente quando `is_promotional=True`.
  3. O provedor **DEVE** estruturar a árvore MIME com `text/plain` (`set_content`, com fallback automático caso `plain_text` não seja fornecido) antes de `text/html` (`add_alternative`), ignorar anexos para referências `http://` ou `https://`, resolver caminhos locais de forma modular contra `assets_dir` (`EMAIL_ASSETS_DIR`, degradando graciosamente com aviso em log caso a pasta não exista em clones *open source*) e anexar referências locais existentes (incluindo `*_q75.webp` como `image/webp`) via `add_related` com `Content-ID` e `Content-Disposition: inline`.
  4. O provedor **DEVE** mascarar endereços de e-mail em todos os logs via `_mask_email()` (preservando `MACRO_EMAIL_MASK_VISIBLE_PREFIX_CHARS` = `5` caracteres iniciais e o último antes do `@` para prefixos > 6 chars).
  5. Após cada envio bem-sucedido, **DEVE** aguardar `MACRO_SMTP_THROTTLE_DELAY_SEG` (`2.0s`); em falhas transitórias (`SMTPServerDisconnected`, `SMTPException`, `OSError`, `TimeoutError`), **DEVE** retentar até `MACRO_SMTP_MAX_RETRIES` (`3`) vezes com backoff linear progressivo (`5.0s * tentativa`) e retornar `False` ao esgotar tentativas.
  6. O método `close()` **DEVE** encerrar a conexão SMTP ativa sob `self._lock` invocando `quit()` com fallback para `close()` se `quit()` falhar, resetando `self._server = None`.
- **Cenário Verificável:**
  - **DADO** uma conexão SMTP ativa e uma falha em `server.quit()`
  - **QUANDO** `provider.close()` é chamado
  - **ENTÃO** o fallback `server.close()` é executado e `provider._server` torna-se `None`.

---

### `REQ-07` — Worker de Pedidos (STG): Âncora Temporal, Regras de Transição e Bloqueios
- **Módulos:** [`src/workers/orders.py`](../src/workers/orders.py)
- **Testes:** [`tests/test_orders.py`](../tests/test_orders.py), [`tests/test_customer_extraction.py`](../tests/test_customer_extraction.py)
- **Requisito (EARS):**
  1. `OrderProcessor.process()` **DEVE** consultar `get_orders(include=['customer', 'items', 'status', 'shipments', 'transactions'])` e interromper a paginação quando `_precheck_order` encontrar pedido com idade superior a `MACRO_PRECHECK_MAX_DAYS` (`15` dias).
  2. `_precheck_order` **DEVE** desqualificar pedidos sem `created_at.date` ou com timezone inválido (`should_continue=True, is_eligible=False`). Quando `config.MAX_WORKERS <= 1`, o worker **DEVE** processar pedidos sequencialmente (modo debug síncrono); caso contrário, **DEVE** usar `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)`.
  3. O worker **DEVE** ignorar pedidos sem `cart_id` em `metadata.data`, extrair o primeiro nome do cliente (fallback `"Cliente"`) e selecionar o `item_sku` (fallback `sku.data.sku`) do item de maior preço para persistência.
  4. Para definição de `data_pedido`, o worker **DEVE** usar `order.get("created_at")` como fonte primária, com fallback para `transactions[0].created_at` e depois `order.get("updated_at")`, e após o `upsert_from_order` **DEVE** recalcular todos os intervalos usando `row["data_pedido"]` retornado pelo banco normalizado para UTC.
  5. O worker **DEVE** pular imediatamente registros em estado terminal `stg ∈ {3, 8, 95, 96, 97}` (nota: `STG=1` não é pulado para permitir evolução `1 → 3` em `on_carriage`).
  6. O mapeamento de status Yampi **DEVE** seguir: `is_refunded = (alias == 'refunded')` (Prioridade 1 → `STG 8`); `is_on_carriage = (alias == 'on_carriage')` (Prioridade 2 → `STG 3`); `is_paid` (`is_on_carriage` ou `status_id ∈ {4,5,6,7,9}` ou `alias ∈ {'paid','in_separation','invoiced','ready_for_shipping','shipped','delivered'}`); `is_pending` (`status_id ∈ {1,2,3}` ou `alias ∈ {'created','authorized','waiting_payment'}`); `is_cancelled` (`status_id ∈ {8,12}` ou `alias ∈ {'cancelled','refunded'}`). Pedidos cancelados precocemente (`is_cancelled` com `stg is None` e `diff <= 30 min`) aguardam o timeout para entrar em `STG 4`.
  7. A transição para `STG 3` (tanto via `on_carriage` quanto via `is_paid` após `stg ∈ {2, 4, 5, 6, 7}`) **DEVE** ser bloqueada caso `_get_tracking_code(order)` (precedência: `order.track_code` → `order.tracking_code` → `shipments[0].track_code` → `shipments[0].tracking_code`) não encontre código de rastreio não vazio.
  8. Quando `template_name` e `email` estiverem presentes e `NotificationService.handle_transition` retornar `False`, o worker **DEVE** abortar `update_stg`, mantendo o estado anterior para retentativa no ciclo seguinte; se não houver `template_name` ou `email`, `update_stg` é gravado sem disparo de e-mail.
  9. A cada transição gravada, **DEVE** registrar breadcrumb `order_state_machine` no Sentry com `{"order_id", "cart_id", "new_stg", "previous_stg"}`.

---

### `REQ-08` — Worker de Carrinhos Abandonados (STC): Âncora `updated_at` e Congelamento
- **Módulos:** [`src/workers/abandoned_cart.py`](../src/workers/abandoned_cart.py)
- **Testes:** [`tests/test_abandoned_cart.py`](../tests/test_abandoned_cart.py)
- **Requisito (EARS):**
  1. `AbandonedCartProcessor.process()` **DEVE** consultar `get_abandoned_carts(include=['customer', 'items'])` (sem `transactions`).
  2. Tanto no `_precheck_cart` quanto no cálculo de `data_carrinho`, o worker **DEVE** usar `cart.get("updated_at") or cart.get("created_at")`, interrompendo a busca ao exceder `MACRO_PRECHECK_MAX_DAYS` (`15` dias). Quando `config.MAX_WORKERS <= 1`, processa sequencialmente; caso contrário, utiliza `ThreadPoolExecutor(max_workers=config.MAX_WORKERS)`.
  3. O worker **DEVE** extrair defensivamente os dados do cliente (`customer.data` ou `customer`), ignorar carrinhos sem e-mail válido antes do upsert, selecionar o SKU do item de maior preço e, após `upsert_from_cart`, normalizar `row["data_carrinho"]` retornado pelo banco para UTC antes de avaliar os timers STC.
  4. Se `row.get("order_id") is not None`, o worker **DEVE** abortar o processamento imediatamente, preservando o `stc` congelado.
  5. O worker **DEVE** pular estados terminais `stc ∈ {18, 85, 86, 87}` e aplicar a régua `None → 15 (>4h)`, `15 → 16 (>24h)`, `16 → 17 (>48h)`, `17 → 18 (>96h)`.
  6. Quando `NotificationService.handle_cart_transition` retornar `False`, o worker **DEVE** abortar `update_stc` para retentativa automática no próximo ciclo.
  7. A cada transição gravada, **DEVE** registrar breadcrumb `cart_state_machine` no Sentry com `{"cart_id", "new_stc", "previous_stc"}`.

---

### `REQ-09` — Serviço de Notificação, Builders de E-mail e Paridade `text/plain`
- **Módulos:** [`src/services/notification_service.py`](../src/services/notification_service.py), [`src/services/email_builders/base_builder.py`](../src/services/email_builders/base_builder.py), [`src/services/email_builders/concrete_builders.py`](../src/services/email_builders/concrete_builders.py), [`src/templates/emails/config/brand_data.yml`](../src/templates/emails/config/brand_data.yml)
- **Testes:** [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py), [`tests/test_orders.py`](../tests/test_orders.py), [`tests/test_abandoned_cart.py`](../tests/test_abandoned_cart.py), [`tests/test_email_plain_text.py`](../tests/test_email_plain_text.py)
- **Requisito (EARS):**
  1. `BaseEmailBuilder._build_items_html` **DEVE** calcular o preço unitário na ordem `sku.data.price_discount` → `sku.data.price_sale` → `item.price` → `item.product_price` → `0.0`, calcular `soma_sem_frete = calculated_subtotal - discount` e aplicar a regra de **frete grátis** quando `soma_sem_frete >= 200.0` (desconsiderando o custo de frete do `final_total`).
  2. Os builders **DEVEM** renderizar templates Jinja2 (`autoescape=True`) combinados com `brand_data.yml` (usando assuntos neutros sem emojis/urgência e ativos `*_q75.webp`), extrair `pix_code` (`pix.data[0]`, `pix.data` ou `pix[0]`), definir `tracking_code` fallback como `'Disponível em breve'` quando `new_stg == 3` (ou `'Aguardando envio'` nos demais estados), resolver `tracking_url` (`order.track_url` → `order.tracking_url` → `shipment.track_url` → `shipment.tracking_url` → `customer.login_url` → `brand_data.store_url`) e `recovery_url` (pedidos: `checkout_url` → `public_url` → `reorder_url` → `""`; carrinhos: `simulate_url` → `recovery_url` → `checkout_url` → `"https://yampi.com.br"`).
  3. `BaseEmailBuilder.build_with_plain_text(event)` **DEVE** gerar `(subject, html_body, plain_text)` utilizando `html_to_plain_text()`, removendo blocos `<style>`, `<script>`, `<head>`, `<title>` e condicionais MSO e preservando links `https://`, itens, valores, PIX/rastreio e rodapé com CNPJ.
  4. `NotificationService` **DEVE** acionar `build_with_plain_text(event)` e repassar `plain_text` e `is_promotional` (`True` para `cupom_pedido_1..3` e carrinhos abandonados; `False` para `pedido_aprovado`, `pedido_pendente` e `pedido_a_caminho`) para `provider.send_email_message(...)`.
  5. Quando `MACRO_ENABLE_LOCAL_HTML_SAVING` estiver ativo, `NotificationService` **DEVE** persistir o HTML renderizado em `local_data/emails/order_<id>/` ou `local_data/emails/cart_<id>/`.
  6. Quando `MACRO_FORCE_TEST_EMAIL_RECIPIENT` for `True`, todos os disparos **DEVEM** ser redirecionados para `config.TEST_EMAIL_RECIPIENT`.
  7. Quando `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH` for `True` e o destinatário for diferente de `TEST_EMAIL_RECIPIENT`, o serviço **DEVE** disparar uma cópia idêntica de supervisão após o envio principal bem-sucedido (mantido `False` por padrão em produção para prevenir *Graymail*).
  8. `NotificationService` **DEVE** suportar exatamente 6 builders de pedido (`pedido_aprovado`, `pedido_pendente`, `pedido_a_caminho`, `cupom_pedido_1`, `cupom_pedido_2`, `cupom_pedido_3`) e 3 de carrinho (`carrinho_abandonado_cupom4`, `carrinho_abandonado_cupom5`, `carrinho_abandonado_cupom6`); caso o template não possua builder registrado ou não haja destinatário válido, **DEVE** retornar `False`.

---

### `REQ-10` — Orquestração, Ciclo de Vida de Recursos e Daemon Contínuo
- **Módulos:** [`src/main.py`](../src/main.py), [`src/daemon.py`](../src/daemon.py)
- **Testes:** [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. `get_dependencies()` **DEVE** selecionar `DryRunMessageProvider` quando `MACRO_ENABLE_REAL_EMAIL_DISPATCH` for `False` e exigir `SMTP_USER` e `SMTP_PASSWORD` quando `True` (encerrando com `sys.exit(1)` se ausentes).
  2. `run_abandoned_carts()`, `run_orders()` e `run_all()` **DEVEM** executar `_close_resources(state_repo, message_provider)` dentro de bloco `finally:` para garantir encerramento do pool PostgreSQL e da conexão SMTP mesmo diante de exceções nos workers.
  3. `daemon.main()` **DEVE** executar `run_all()` continuamente em intervalos de `MACRO_DAEMON_SLEEP_INTERVAL_SEG` (`300s`), encapsulado em `sentry_sdk.crons.monitor(monitor_slug="yampi-daemon-cycle")` quando disponível, capturando exceções não tratadas do ciclo sem derrubar o loop principal.

---

### `REQ-11` — Servidor de Webhooks (Meta WhatsApp Cloud API)
- **Módulos:** [`src/webhook_server.py`](../src/webhook_server.py)
- **Testes:** [`tests/test_main_and_daemon.py`](../tests/test_main_and_daemon.py)
- **Requisito (EARS):**
  1. Quando `SENTRY_DSN` estiver configurado no ambiente, o servidor Flask **DEVE** inicializar o Sentry com `FlaskIntegration()` e `send_default_pii=False`, escutando na porta `MACRO_WEBHOOK_SERVER_PORT` (`5000`).
  2. Em `GET /webhook`, se `hub.mode == "subscribe"` e `hub.verify_token == MACRO_META_WEBHOOK_VERIFY_TOKEN`, o servidor **DEVE** retornar `hub.challenge` com HTTP `200`; caso contrário, **DEVE** retornar HTTP `403`.
  3. Em `POST /webhook`, o servidor **DEVE** processar eventos de `messages` e `statuses` (com resiliência a payloads inesperados) e responder `"EVENT_RECEIVED"` com HTTP `200`.

---

### `REQ-12` — Políticas de Entregabilidade, Compressão WebP 75% e Governança DNS/Antispam
- **Módulos:** Pipeline offline de otimização WebP 75%, [`src/templates/emails/config/brand_data.yml`](../src/templates/emails/config/brand_data.yml), [`src/ports/smtp_email_provider.py`](../src/ports/smtp_email_provider.py)
- **Especificação Dedicada:** [`docs/email_deliverability_policies.md`](./email_deliverability_policies.md)
- **Requisito (EARS):**
  1. As 22 imagens de templates **DEVEM** utilizar formato WebP otimizado (`*_q75.webp` com fundo branco `#FFFFFF` em transparências, total de 524,3 KB / redução de 96,3% sobre os originais em backup externo) e preferencialmente estar hospedadas em endpoint HTTPS público/CDN; enquanto permanecerem em armazenamento local, trafegam inline (`image/webp`) com impacto de payload reduzido.
  2. O domínio emissor (`elevemeloja.com.br`) **DEVE** manter `SPF` com `-all`, `DKIM` RSA 2048 bits ativo, `DMARC` coercivo (`p=quarantine`/`p=reject`, `pct=100`, `adkim=r; aspf=r;`, `rua=` ativo, sem `ruf=`) e monitoramento contínuo no Google Postmaster Tools (`< 0,10%` de taxa de spam).

---

### `REQ-13` — Roteamento Dual de Remetentes SMTP (`oficial@` vs. `comercial@`)
- **Módulos:** [`src/ports/smtp_email_provider.py`](../src/ports/smtp_email_provider.py), [`src/services/notification_service.py`](../src/services/notification_service.py), [`src/core/config.py`](../src/core/config.py), [`src/core/macros.py`](../src/core/macros.py)
- **Testes:** [`tests/test_dual_sender_routing.py`](../tests/test_dual_sender_routing.py)
- **Requisito (EARS):**
  1. Quando `is_promotional=False` (`pedido_aprovado`, `pedido_pendente`, `pedido_a_caminho`), o `SMTPEmailProvider` **DEVE** autenticar e despachar pelo pool transacional principal (`_server`, `SMTP_USER`/`SMTP_FROM` = `oficial@elevemeloja.com.br`) sem cabeçalhos `List-Unsubscribe`.
  2. Quando `is_promotional=True` (`cupom_pedido_1..3` e `carrinho_abandonado_cupom4..6`) e `PROMO_SMTP_USER`/`PROMO_SMTP_PASSWORD` estiverem configurados, o provedor **DEVE** autenticar e despachar pelo pool promocional isolado (`_promo_server`, `PROMO_SMTP_FROM` = `comercial@elevemeloja.com.br`, com fallback automático para `PROMO_SMTP_USER`), injetando `List-Unsubscribe` e `List-Unsubscribe-Post: List-Unsubscribe=One-Click`.
  3. Quando `PROMO_SMTP_USER` ou `PROMO_SMTP_PASSWORD` estiver ausente, o provedor **DEVE** realizar fallback transparente para `_server`, preservando os cabeçalhos RFC 8058.
  4. Em todos os fluxos, `Reply-To` **DEVE** apontar para `EMAIL_REPLY_TO` (`"Atendimento Eleveme" <comercial@elevemeloja.com.br>`), falhas em um pool SMTP **NÃO DEVEM** corromper o pool do outro canal sob `self._lock`, e `close()` **DEVE** encerrar ambos os pools com tolerância a exceções em `quit()`/`close()`.
- **Cenário Verificável:**
  - **DADO** um `SMTPEmailProvider` configurado com `oficial@elevemeloja.com.br` (principal) e `comercial@elevemeloja.com.br` (promocional)
  - **QUANDO** `NotificationService` dispara `pedido_aprovado` e `cupom_pedido_1` (inclusive sob concorrência em `ThreadPoolExecutor`)
  - **ENTÃO** `pedido_aprovado` sai por `_server` (`oficial@`, sem `List-Unsubscribe`) e `cupom_pedido_1` sai por `_promo_server` (`comercial@`, com `List-Unsubscribe: One-Click`).

---

### `REQ-14` — Telemetria, Métricas e Rastreamento de Falhas de Disparo de E-mail (Sentry + LGPD)
- **Módulos:** [`src/core/telemetry.py`](../src/core/telemetry.py), [`src/ports/smtp_email_provider.py`](../src/ports/smtp_email_provider.py), [`src/services/notification_service.py`](../src/services/notification_service.py), [`src/main.py`](../src/main.py), [`src/debug_main.py`](../src/debug_main.py)
- **Testes:** [`tests/test_email_telemetry.py`](../tests/test_email_telemetry.py)
- **Requisito (EARS):**
  1. `src/core/telemetry.py` **DEVE** expor as constantes canônicas `METRIC_EMAIL_DISPATCH_STARTED` (`"email.dispatch.started"`), `METRIC_EMAIL_DISPATCH_SENT` (`"email.dispatch.sent"`) e `METRIC_EMAIL_DISPATCH_FAILED` (`"email.dispatch.failed"`), emitindo contadores via `sentry_sdk.metrics.count(..., 1, attributes=...)` com remoção de atributos `None` e política **Zero-Crash** (nenhuma falha do SDK ou ausência de DSN pode interromper o envio).
  2. Os *context managers* `email_dispatch_scope(...)` e `start_smtp_span(...)` (`op="email.smtp.send"`) **DEVEM** isolar contexto/tags/atributos por disparo e propagar integralmente todas as exceções lançadas pelo bloco interno (`yield`), realizando *fallback* limpo apenas quando a abertura/configuração no `sentry_sdk` falhar.
  3. Em estrita conformidade LGPD (`send_default_pii=False`), `extract_recipient_domain()`, `sanitize_error_message()`, `extract_smtp_error_details()` e o `event_processor` de `capture_email_dispatch_error()` **DEVEM** garantir que nenhum endereço de e-mail completo (cru), nome do cliente, CPF, senha SMTP ou corpo HTML apareça em métricas, tags, spans, breadcrumbs (`smtp.retry`), contextos (`email_dispatch`, `smtp_dispatch`) ou payloads de *issues* (incluindo mensagens de exceção e variáveis de *stacktrace*).
  4. `SMTPEmailProvider.send_email_message()` **DEVE** emitir `email.dispatch.started` uma única vez antes do `try` principal, envolver cada tentativa SMTP em `start_smtp_span()`, validar retornos `refused` não vazios de `sendmail()` convertendo-os em `SMTPRecipientsRefused` com endereço mascarado, emitir `email.dispatch.sent` imediatamente após confirmação de aceitação pelo servidor (e **antes** do `time.sleep` de *throttling*), registrar breadcrumbs `smtp.retry` por tentativa falha e, ao esgotar retentativas (`smtp_retries_exhausted`) ou ocorrer erro fatal (`smtp_fatal`), emitir `email.dispatch.failed`, capturar exatamente **1** *issue* via `capture_email_dispatch_error()` preservando o *traceback* completo e registrar `logger.error(..., exc_info=...)` com a mesma instância de exceção para deduplicação automática via `DedupeIntegration`.
  5. `NotificationService` **DEVE** abrir `email_dispatch_scope` com `dispatch_kind="primary"` para pedidos (`flow="order"`, `STG_*`, `order_id`, `order_number`, `cart_id` extraído de `metadata.data`) e carrinhos (`flow="abandoned_cart"`, `STC_*`, `cart_id`), abrir escopo separado com `dispatch_kind="duplicate"` no envio de supervisão, capturar falhas de montagem do template (`failure_stage="template_build"`) emitindo `started` + `failed` + *traceback*, e registrar falha retornada pelo provedor via `logger.warning()` (evitando segunda *issue* sem *traceback* pela `LoggingIntegration`). `DryRunMessageProvider` **NÃO DEVE** emitir métricas `email.dispatch.*`.
  6. `main._close_resources()` (em bloco tolerante a falhas) e `debug_main.py` **DEVEM** invocar `flush_telemetry()` ao término da execução.
- **Cenário Verificável:**
  - **DADO** um disparo em `NotificationService` via `SMTPEmailProvider` com `sendmail()` retornando `{"vitima@gmail.com": (550, b"5.1.1 User unknown")}` ou levantando `SMTPAuthenticationError`
  - **QUANDO** as retentativas SMTP se esgotam e `flush_telemetry()` é executado
  - **ENTÃO** são emitidos `email.dispatch.started` (1), `email.dispatch.sent` (0), `email.dispatch.failed` (1), breadcrumbs `smtp.retry`, e exatamente **1** *issue* no Sentry com *traceback* completo, contextos `email_dispatch` + `smtp_dispatch` (`retry_history`) e zero ocorrência de `"vitima@gmail.com"` nos payloads enviados.
  - **DADO** um disparo bem-sucedido no `SMTPEmailProvider` ou falha interna no `sentry_sdk`
  - **QUANDO** `sendmail()` confirma envio (retornando `{}`) antes do `time.sleep` ou `sentry_sdk.metrics.count` lança erro em runtime
  - **ENTÃO** `email.dispatch.sent` é emitido antes do *throttling* no sucesso, `send_email_message` retorna `True` sem lançar erro de telemetria, e exceções de negócio dentro de `email_dispatch_scope`/`start_smtp_span` continuam propagando normalmente.

---

## 3. Decisões Arquiteturais Leves (ADRs de Manutenção Pré-Deploy)

### ADR-01: Proteção Anti-Regressão Temporal (`COALESCE(LEAST(...))` + Normalização UTC)
- **Contexto:** Atualizações posteriores na Yampi (ex.: alteração manual ou novo evento de status/transação) podiam sobrescrever `data_pedido` ou `data_carrinho` com timestamps mais recentes, reiniciando as janelas de cupons e gerando envios fora de hora. Além disso, colunas `TIMESTAMP` sem timezone no PostgreSQL retornam `datetime` *naive* no `psycopg2`.
- **Alternativas Consideradas:** Ignorar atualização da data no conflito (`DO NOTHING` na data) vs `COALESCE(LEAST(atual, novo), novo)`.
- **Decisão:** Adotar `COALESCE(LEAST(...))` no `ON CONFLICT` em `postgres_repo.py` e normalizar explicitamente o campo retornado pelo banco para UTC nos workers (`orders.py` e `abandoned_cart.py`), mantendo `created_at` como fonte primária para pedidos e `updated_at` (fallback `created_at`) para carrinhos.
- **Consequências:** Garante monotonicidade da âncora temporal mesmo se chegarem eventos fora de ordem, mantendo compatibilidade total com schemas `TIMESTAMP` existentes sem exigir migração DDL imediata.

### ADR-02: Encerramento Determinístico de Recursos (`_close_resources` + `SMTPEmailProvider.close()`)
- **Contexto:** O `daemon.py` executa `run_all()` a cada 5 minutos, instanciando um novo `ThreadedConnectionPool` e um novo `SMTPEmailProvider` por ciclo. Sem fechamento explícito, pools e conexões SMTP poderiam vazar descritores de arquivo ou conexões TCP ao longo de dias de operação.
- **Decisão:** Implementar `close()` thread-safe em `SMTPEmailProvider` e encapsular `run_abandoned_carts()`, `run_orders()` e `run_all()` em blocos `try / finally` chamando `_close_resources(state_repo, message_provider)`.
- **Consequências:** Zero vazamento de sockets TCP ou conexões do PostgreSQL entre ciclos do daemon.

### ADR-03: Inicialização Idempotente do Sentry e `SafeRotatingFileHandler`
- **Contexto:** Chamadas repetidas a `setup_logging()` (como importação encadeada `daemon.py` → `main.py` ou cenários de teste) reinicializavam `sentry_sdk.init()`. Adicionalmente, se a pasta de logs montada via bind mount fosse limpa durante a execução, o `RotatingFileHandler` padrão falhava ao emitir novos registros.
- **Decisão:** Proteger `sentry_sdk.init()` com flag `_SENTRY_INITIALIZED` e introduzir `SafeRotatingFileHandler`, que valida/recria o diretório e reseta `self.stream` caso o arquivo seja removido em runtime.
- **Consequências:** Observabilidade resiliente a limpezas operacionais de disco e sem re-inicialização redundante do SDK.

### ADR-04: Modernização MIME (`EmailMessage`), Compressão Visual WebP 75% e Conformidade RFC 5322/8058
- **Contexto:** O envio original via `MIMEMultipart` sem `Message-ID`, `Date` ou parte `text/plain`, somado a PNGs inline de até 1,8 MB, assuntos com emojis/caixa alta e envio em duplicata (`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = True`), acumulava penalidades severas no SpamAssassin e violava os requisitos de remetentes de Google/Yahoo/Microsoft (2024+).
- **Decisão:** Migrar `SMTPEmailProvider` para `email.message.EmailMessage` com `text/plain` precedendo `text/html`, injeção de `Message-ID`/`Date`/`From`/`Reply-To` e `List-Unsubscribe: One-Click` para fluxos promocionais, comprimir as imagens para WebP 75% (`*_q75.webp` com composição em fundo branco sólido `#FFFFFF` para transparências, mantendo transição preparada para endpoint HTTPS externo), higienizar templates/assuntos e desativar o envio em duplicata, complementados pelo endurecimento DNS (`SPF -all` e `DMARC p=quarantine`).
- **Consequências:** Eliminação dos pontos de penalidade estrutural e redução de 97,0% do peso dos ativos visuais, mantendo retrocompatibilidade total com `SMTPEmailProvider` e prontidão automática para hospedagem em CDN/HTTPS.

### ADR-05: Roteamento Dual de Remetentes SMTP (`oficial@` vs. `comercial@`)
- **Contexto:** Disparos promocionais e de recuperação de carrinho possuem padrão de engajamento distinto dos avisos transacionais essenciais (`pedido_aprovado`, `pedido_pendente`, `pedido_a_caminho`). Compartilhar a mesma caixa remetente e pool SMTP arrisca degradar a reputação dos avisos operacionais caso campanhas promocionais recebam menor taxa de abertura.
- **Alternativas Consideradas:** Manter conta SMTP única para todos os 9 templates vs. instanciar múltiplos providers separados nos workers vs. gerenciar dois pools independentes (`_server` e `_promo_server`) no `SMTPEmailProvider` via sinalizador `is_promotional`.
- **Decisão:** Adotar pools independentes (`_server` para `SMTP_*` / `oficial@` e `_promo_server` para `PROMO_SMTP_*` / `comercial@`) dentro do `SMTPEmailProvider` sob o mesmo `threading.Lock`, com fallback transparente para `_server` quando credenciais promocionais estiverem ausentes e `Reply-To` unificado em `EMAIL_REPLY_TO`.
- **Consequências:** Isola a reputação do canal transacional sem alterar a assinatura dos workers ou quebrar compatibilidade com instalações que configuram apenas o SMTP principal, mantendo o isolamento de falhas entre canais e encerramento determinístico de ambos os pools em `close()`.

### ADR-06: Telemetria de Disparos no Sentry via Application Metrics (`count`), `new_scope()` e Sanitização LGPD em Stacktraces
- **Contexto:** Era necessário contabilizar com precisão o volume diário de e-mails enviados com sucesso, detectar envios iniciados sem desfecho (travamentos/quedas abruptas) e capturar *tracebacks* completos com contexto de negócio para reprodução de falhas, mantendo `send_default_pii=False` (LGPD) e sem quebrar o contrato `MessageProviderProtocol` (nem mocks existentes). Adicionalmente, descobriu-se que falhas após retentativas no `SMTPEmailProvider` eram registradas apenas via `logger.error` sem `exc_info`, enquanto `NotificationService` gerava uma segunda *issue* duplicada sem *traceback*, e o `sentry-sdk` incluía HTML e `customer_data` em `frame["vars"]`.
- **Alternativas Consideradas:** Alterar `send_email_message(...)` para receber `**kwargs` de negócio (quebraria mocks/contratos), contar via `logger.info` apenas (sem agregação confiável nem *trace_id*), ou criar módulo central Zero-Crash com `sentry_sdk.metrics.count` + escopo isolado por thread (`new_scope()`).
- **Decisão:** Centralizar a observabilidade em `src/core/telemetry.py` com três contadores (`email.dispatch.started`, `email.dispatch.sent` após validação de `refused` e antes do *throttling*, e `email.dispatch.failed`), span `email.smtp.send`, isolamento por disparo via `email_dispatch_scope(...)` no `NotificationService`, sanitização incondicional de `frame["vars"]` e múltiplos e-mails via *event processor*, `logger.warning` no `NotificationService` e `exc_info` preservado para deduplicação via `DedupeIntegration`, além de `flush_telemetry()` no `_close_resources()` de `main.py` e no fim de `debug_main.py`.
- **Consequências:** Visibilidade diária e por template/canal no Sentry Metrics Explorer correlacionada por `trace_id` com *issues* únicas e acionáveis, sem vazamento de PII e sem quebra de interfaces ou risco à entrega de e-mails.
