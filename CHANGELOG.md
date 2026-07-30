# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [5.1.0] - 2026-07-30 (Clareza em Macros de Disparo e Teste)

### Adicionado / Modificado
- **Refatoração dos Comentários e Documentação de Macros**:
  - Esclarecida a interação entre `MACRO_ENABLE_REAL_EMAIL_DISPATCH` (controle de transporte SMTP) e `MACRO_FORCE_TEST_EMAIL_RECIPIENT` (controle de destinatário de teste).
  - Atualizado `README.md`, `src/core/README.md` e `src/core/macros.py` para evitar ambiguidades no comportamento dos envios de homologação.

---

## [5.0.0] - 2026-07-30 (Centralização de Mocks e Entrypoints)

### Adicionado / Modificado
- **Novo Arquivo Inicializador Oficial (`src/daemon.py`)**:
  - O `daemon.py` torna-se a forma documentada e oficial de iniciar o serviço contínuo do sistema. Removida configuração estática interna dele.
- **Centralização de Flags de Depuração em `macros.py`**:
  - Removidas lógicas de terminal (flags `--production` CLI no `main.py`).
  - Adicionada a flag independente `MACRO_ENABLE_REAL_EMAIL_DISPATCH` para orquestrar se os e-mails sairão via SMTP ou apenas Mock no terminal.
  - Adicionada a flag independente `MACRO_ENABLE_LOCAL_HTML_SAVING` para orquestrar se o HTML formatado deve ou não ser salvo no disco local (pasta `local_data/emails/`).
- **Atualização na Documentação**:
  - Refatorados `README.md` e `docs/project_overview.md` para alertar usuários de que as alterações da aplicação devem ser feitam em `src/core/macros.py`.

---

## [4.2.2] - 2026-07-30 (Tratamento Global de Erros e Observabilidade)

### Adicionado / Modificado
- **Interceptação Global de Erros (`sys.excepthook` e `threading.excepthook`)**:
  - Implementado tratamento global na configuração de log (`src/core/logging_config.py`) para capturar toda e qualquer exceção não tratada na aplicação.
  - Se um erro crítico escapar de todos os `try...except`, ele será gravado no `app.log` com o **Traceback completo** sob a tag `FATAL ERROR` antes do shutdown do sistema.
- **Blindagem de Threads Assíncronas**:
  - Os *Generators* de `executor.map` em `orders.py` e `abandoned_cart.py` agora são consumidos ativamente via cast para `list()`. Isso garante que eventuais vazamentos de exceções profundas nas threads de *ThreadPoolExecutor* sejam jogados para a thread principal e detectados pelo interceptador global.
- **Documentação de Roadmap (`FUTURE_IMPLEMENTATION.md`)**:
  - Oficializada a obrigatoriedade futura para integrações com **Sentry/Datadog** e formatação de logs paralela em **JSON**.

---

## [4.2.1] - 2026-07-30 (Correção de Tipagem de API e Prevenção de Falhas)

### Corrigido
- **Falha Fatal de Processamento PIX e Rastreios**:
  - Corrigido o `AttributeError: 'list' object has no attribute 'get'` no `base_builder.py` que derrubava a esteira de envios.
  - O código de extração para nós nativos da Yampi (`pix` e `shipments`) agora utiliza lógicas defensivas de validação de tipo (`isinstance`), pois a API envia relacionamentos *has-many* de forma polimórfica (ora como array, ora omitindo chaves).
  - A Chave PIX é extraída do primeiro item do array de dados com fallback de segurança para e-mails de Boletos e Cartões (onde o QR Code fica propositalmente vazio).

---

## [4.2.0] - 2026-07-27 (Modernização UI de E-mails e Refatoração de Assets)

### Adicionado / Modificado
- **Reestruturação de Assets (`src/templates/emails/mjml_src/images/`)**:
  - Organização sequencial em 9 pastas (de `email_1_pedido_aprovado` a `email_9_carrinho_abandonado_6`).
  - Remoção de caracteres especiais (`%`) nos nomes de arquivos de imagem para garantir compatibilidade de renderização offline (`file:///`).
- **Validação de Frete na Tabela de Produtos**:
  - Implementada lógica no `BaseEmailBuilder` que adiciona dinamicamente o valor do frete ao subtotal, exceto quando o valor puro dos produtos for superior a R$ 200,00 (frete grátis implícito).
- **Injeção de Cupom Dinâmica**:
  - Template Jinja2 agora extrai a variável `value_cupom` diretamente do `brand_data.yml` para todos os templates de descontos.
- **Botões e UX**:
  - Alteração do link de call-to-action nos e-mails Pós-Venda (`cupom_pedido_1..3`) de `checkout_url` para a Homepage da loja (`store_url`), para facilitar o reengajamento.
  - O botão do e-mail `carrinho_abandonado_cupom5` (15% OFF) recebeu nova cor (`#EA580C`) e nova classe de sombra (`btn-shadow-orange`).
- **Novo Layout PIX**:
  - O e-mail de "Pedido Pendente" (`pedido_pendente.mjml`) recebeu nova UI para exibição da Chave PIX Copia e Cola, encapsulada em caixa tracejada.
- **Email Mock Generator**:
  - Suporte completo ao novo esquema de diretórios sequenciais, resolvendo paths locais para HTML absoluto para revisão offline.

---

## [4.1.0] - 2026-07-27 (Tabela de Produtos Dinâmica nos E-mails)

### Adicionado / Modificado
- **Tabela de Produtos Dinâmica nos E-mails (`06_products_table.md`)**:
  - Renderização tabular stateless de itens, quantidade, frete e valor total extraídos diretamente dos payloads JSON da Yampi.
  - Alinhamento visual por colunas (Item, Quantidade, Preço) e estilização adaptada ao Eleveme Email UI Design System.
- **Documentação e Decisões**:
  - Registrada e implementada a especificação `06_products_table.md` (v4.1.0).

---

## [4.0.0] - 2026-07-27 (Nova Engine MJML + Jinja2 e Brand Data Fonte Zero)

### Adicionado / Modificado (Major Release)
- **Engine MJML & Jinja2 Nativo**:
  - Nova suite de 9 templates de e-mail responsivos compilados via MJML (`src/templates/emails/mjml_src/`).
  - `BaseEmailBuilder` e `ConcreteBuilders` integrados nativamente com Jinja2 em tempo de execução.
- **`brand_data.yml` como Fonte de Informação Zero**:
  - Centralização absoluta de textos, subjects, informações da empresa, links de redes sociais e rotas de imagens/ícones locais e CDN.
  - Eliminados 100% dos caminhos hardcoded e fallbacks de imagem em código Python.
- **Nomenclatura Agnostica de Cupons**:
  - Cupons de Pedidos renomeados para `cupom_pedido_1..3`.
  - Cupons de Carrinho Abandonado renomeados para `carrinho_abandonado_cupom4..6`.
- **Utilitário de Mocks Locais**:
  - Script `email_mock_generator.py` migrado para `src/templates/emails/mjml_src/` para testes visuais offline.
- **Documentação e Decisões**:
  - Registrada a decisão `05_email_refactor.md` e o manual `src/templates/emails/mjml_src/README.md`.



---

## [3.2.0] - 2026-07-27 (Validação de Código de Rastreio para Transição STG 3)

### Corrigido
- **Bloqueio de Transição para STG 3 sem Código de Rastreio (`src/workers/orders.py`)**:
  - A transição para `STG 3` agora exige estritamente a presença prévia de um código de rastreio válido no payload da Yampi.
  - Se um pedido mudar para `paid` ou `on_carriage` sem o código de rastreio, a transição para `STG 3` fica bloqueada e o pedido permanece no estado atual (ex: `2` ou `null`) para novas tentativas nas rodadas seguintes de polling.

---

## [3.1.0] - 2026-07-24 (Ajuste de Controle de Rastreio por Estado)

### Alterado / Corrigido
- **Ajuste de Valores de Controle e Nível de Logging de Rastreio (`src/services/email_builders/base_builder.py`)**:
  - Removido o log falso-positivo de `ERROR` durante o preenchimento de e-mails em estágios pré-envio (`STG != 3`, ex: `STG 1` de confirmação de pagamento).
  - **Valor de Controle Pré-envio (`STG != 3`)**: Quando o código de rastreio não está presente no payload da Yampi em fases iniciais, assume `'Aguardando envio'` e registra apenas log em nível `DEBUG`.
  - **Validação Estrita de Envio (`STG 3`)**: Na transição para `STG 3` (envio/rastreio), o código de rastreio passa a ser verificado de forma obrigatória. Se não for encontrado na Yampi, assume o fallback `'Disponível em breve'` e dispara um log explícito de erro `[RASTREIO OBRIGATÓRIO]`.

---

## [3.0.0] - 2026-07-23 (Versão de Semi Produção / Protótipo 1)

### Adicionado / Refatorado
- **Daemon Autônomo e Resiliente (`src/daemon.py`)**:
  - Implementado loop infinito que processa carrinhos e pedidos a cada 5 minutos.
  - Modo Dry-Run ativado por padrão em produção simulada para extração segura de dados via HTMLs.
- **Tabela Unificada (`email_status_table`)**: Substituição das tabelas separadas `cart_states` e `order_states` por esquema unificado por `cart_id`.
- **Máquina de Estados Dupla**:
  - **STG (Status Global)**: Controle do fluxo de pedidos (`null, 1, 2, 3, 4, 5, 6, 7, 8, 95, 96, 97`).
  - **STC (Status Carrinho)**: Controle do fluxo de carrinhos abandonados (`null, 15, 16, 17, 18, 85, 86, 87`).
- **Timers Temporais Absolutos e Customizados**: Cálculos temporais baseados diretamente em `data_pedido` (STG) ou `data_carrinho` (STC). Janelas relaxadas para garantir melhor aderência.
- **Processamento Assíncrono em Lote**: Produtor consulta Yampi e divide resultados em arquivos JSON de 100 itens (`orders/` e `carts/`), consumidos e deletados por workers paralelos.
- **Locking Concorrente**: Leitura e gravação no banco com `SELECT FOR UPDATE` para evitar corrupção por acesso simultâneo.
- **Bloco de Macros (`MACRO_*`)**: Configuração centralizada no topo dos arquivos de código para prazos, tamanhos de lote e intervalos.
- **Evolução Docker**:
  - `healthcheck` adicionado no PostgreSQL para prevenir que a aplicação suba antes do banco, eliminando o erro de *Connection refused*.
  - Exportação de logs e e-mails mapeados diretamente no container (`logs_from_container/` e `emails_from_container/`).
  - O arquivo `VERSION` agora é injetado no container, resolvendo o bug `vunknown`.

---

## [2.2.1] - 2026-07-23 (Adição de order_number, Logging e Baseline Estável de E-mails)

### Adicionado
- **Nova Coluna `order_number` em `email_status_table`**:
  - Adicionada a coluna `order_number VARCHAR(255) NOT NULL DEFAULT 'N/A'` para armazenar o número público de transação do pedido (ex: `1200388456451468`).
  - Atualizada a interface do repositório (`StateRepositoryProtocol.upsert_from_order`) e as consultas DDL do PostgreSQL com migration automática (`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`).
  - Criado o índice `idx_email_status_order_number` para consultas de alta velocidade.
  - Atualizado o utilitário `tests/find_by_id.sh` para suportar buscas por `order_number`.
- **Sistema de Logging Centralizado e Configurável (`src/core/logging_config.py`)**:
  - Módulo dedicado `src/core/logging_config.py` com a função `setup_logging(verbose)` para padronizar formatters e handlers.
  - Suporte à flag `-v` / `--verbose` via `argparse` em `src/debug_main.py` para alternar dinamicamente o nível de exibição entre `INFO` e `DEBUG`.
  - Inserção de logs de depuração enriquecidos em `src/workers/orders.py`, reportando idade dos pedidos em dias, `order_id`, `order_number`, `cart_id` e justificativas detalhadas para decisões da máquina de estados (STG).
  - Atualização do `.gitignore` para ignorar a pasta local `logs/`.
- **Mapeamento de Status da Yampi e Envio de Rastreio (`on_carriage` / `shipped`)**:
  - Mapeamento abrangente de status pagos da Yampi (`paid`, `in_separation`, `invoiced`, `on_carriage`, `shipped`, `delivered`).
  - Regra de transição específica para pedidos em transporte: quando o status for **explicitamente `on_carriage`**, avança para **`STG = 3`** e dispara automaticamente o template **`envio_rastreio.html`** preenchido com `{tracking_code}` e `{tracking_url}` extraídos de `shipments`.
  - Tratamento direto de pedidos cancelados/reembolsados (`cancelled`, `refunded`) marcando **`STG = 8`** (terminal).
- **Configuração de Macro de Cache**:
  - Adicionada a macro `MACRO_DEBUG_LIMIT` (em `src/core/macros.py`) para parametrizar o limite de leitura e cache nos testes síncronos.

---

## [2.1.0] - 2026-07-21 (Depuração Interativa e Suporte a .env)

### Adicionado
- **Configuração de Depuração VS Code (.vscode)**:
  - Integração nativa com `.env` via `envFile` em `launch.json`.
  - Perfis padronizados em `launch.json` e limpeza de tasks em `tasks.json`.
- **Modo Interativo por Item no Debug (`debug_main.py`)**:
  - Limite de processamento reduzido para até 10 itens por execução (`orders` e `abandoned-carts`).
  - Navegação interativa síncrona `ENTER` passo a passo para cada pedido e carrinho (`INTERACTIVE_DEBUG`).
- **Persistência de Logs de Debug (`logs/app.log`)**:
  - `debug_main.py` atualizado para gravar saídas diretamente em `logs/app.log`.

---

## [1.0.0] - 2026-07-21 (Versão Atual / Baseline Estável)

### Adicionado
- **Integração Yampi REST API v2**:
  - Autenticação e consulta de pedidos (`/v2/{alias}/orders`) e carrinhos abandonados (`/v2/{alias}/checkout/carts`).
  - Scripts de teste e coleta (`estudos/yampi_api/coleta.sh`).
- **Arquitetura Hexagonal (Ports & Adapters)**:
  - Interfaces no domínio (`src/domain/`).
  - Adaptadores SMTP (`src/ports/smtp_email_provider.py`), WhatsApp Meta Cloud API (`src/ports/whatsapp_meta_provider.py`) e DryRun (`src/ports/message_provider.py`).
- **Persistência de Estado Local (SQLite / PostgreSQL Inicial)**:
  - Controle básico de e-mails já enviados para evitar disparos duplicados.
- **Infraestrutura Docker**:
  - `Dockerfile` e `docker-compose.yml` para execução isolada com PostgreSQL.
- **Servidor Webhook Flask**:
  - Micro-serviço para recepção e validação de Webhooks Meta/WhatsApp (`src/webhook_server.py`).
- **Documentação Decisória de Arquitetura**:
  - Decisões de projeto organizadas em `project_decisions/` (`01_database_yampi_planning.md`, `02_email_architecture.md`, `03_mudanca_arquitetura_emails_e_geral.md`).
