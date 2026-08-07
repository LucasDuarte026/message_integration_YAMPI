# ==============================================================================
#                      MESSAGE INTEGRATION - MACROS & CONFIGURAÇÕES
# ==============================================================================
# Este arquivo centraliza todos os parâmetros de negócio, limites operacionais,
# timeouts de rede, timers de máquina de estado e constantes de infraestrutura.
#
# Estrutura do Arquivo:
#   SEÇÃO 1: Planos de Horários e Timers de Cupons/Abandono (Alta Frequência de Ajuste)
#   SEÇÃO 2: Configurações Médias de Operação, Envio, Infraestrutura e Workers
#   SEÇÃO 3: Constantes Estáticas e Infraestrutura Profunda (Rara Alteração)
# ==============================================================================

# ==============================================================================
# SEÇÃO 1: PLANOS DE HORÁRIOS, TIMERS E CUPONS DE RECUPERAÇÃO
# ==============================================================================
# Configurações comerciais das réguas de relacionamento (E-mails e WhatsApp).
# Altere aqui para mudar os intervalos em que os clientes recebem lembretes e descontos.

# ------------------------------------------------------------------------------
# 1.1. Timers de Pedidos (Fluxo STG)
# ------------------------------------------------------------------------------
MACRO_TIMEOUT_PAGAMENTO_SEG = 30 * 60     # 30 minutos (janela inicial de tolerância de pagamento)
MACRO_DELAY_ORDER_PIX_EMAIL_SEG = 5 * 60  # 5 minutos (delay de segurança antes do Email 2 - PIX pendente)
MACRO_CUPOM_PEDIDO_1_HORAS = 24           # 24 horas (envio do Cupom 1: 10% OFF)
MACRO_CUPOM_PEDIDO_2_HORAS = 48           # 48 horas (envio do Cupom 2: 15% OFF)
MACRO_CUPOM_PEDIDO_3_HORAS = 72           # 72 horas (envio do Cupom 3: 20% OFF)
MACRO_PERDIDO_PEDIDO_HORAS = 96           # 96 horas (marcação final de Pedido Perdido)

# Conversões diretas para segundos consumidas pela máquina de estados (STG)
MACRO_STG_01_TIMER_02 = MACRO_TIMEOUT_PAGAMENTO_SEG
MACRO_STG_04_TIMER_05 = MACRO_CUPOM_PEDIDO_1_HORAS * 3600
MACRO_STG_05_TIMER_06 = MACRO_CUPOM_PEDIDO_2_HORAS * 3600
MACRO_STG_06_TIMER_07 = MACRO_CUPOM_PEDIDO_3_HORAS * 3600
MACRO_STG_07_TIMER_08 = MACRO_PERDIDO_PEDIDO_HORAS * 3600

# ------------------------------------------------------------------------------
# 1.2. Timers de Carrinhos Abandonados (Fluxo STC)
# ------------------------------------------------------------------------------
MACRO_CUPOM_CARRINHO_1_HORAS = 4          # 4 horas (lembrete inicial 15 - Carrinho Abandonado)
MACRO_CUPOM_CARRINHO_2_HORAS = 24         # 24 horas (envio do cupom 16 - 1ª oferta)
MACRO_CUPOM_CARRINHO_3_HORAS = 48         # 48 horas (envio do cupom 17 - 2ª oferta)
MACRO_PERDIDO_CARRINHO_HORAS = 96         # 96 horas (marcação final de Carrinho Perdido)

# Conversões diretas para segundos consumidas pela máquina de estados (STC)
MACRO_STC_00_TIMER_15 = MACRO_CUPOM_CARRINHO_1_HORAS * 3600
MACRO_STC_15_TIMER_16 = MACRO_CUPOM_CARRINHO_2_HORAS * 3600
MACRO_STC_16_TIMER_17 = MACRO_CUPOM_CARRINHO_3_HORAS * 3600
MACRO_STC_17_TIMER_18 = MACRO_PERDIDO_CARRINHO_HORAS * 3600

# Janela máxima de corte precheck (ignora carrinhos/pedidos com mais de X dias no pre-fetch)
MACRO_PRECHECK_MAX_DAYS = 15


# ==============================================================================
# SEÇÃO 2: CONFIGURAÇÕES MÉDIAS (OPERAÇÃO, SERVIDORES, LIMITES E WORKERS)
# ==============================================================================
# Controles operacionais que definem como os processos rodam, conexões e flags de envio.

# ------------------------------------------------------------------------------
# 2.1. Flags de Controle de Disparo de E-mail
# ------------------------------------------------------------------------------
# True  ---> Ativa o provedor SMTP/Meta real. O sistema conecta na rede e despacha mensagens.
# False ---> Modo DRY-RUN (Simulação/Mock). Nenhum e-mail sai para a rede real.
MACRO_ENABLE_REAL_EMAIL_DISPATCH = True

# True  ---> MODO DE HOMOLOGAÇÃO. Força todos os e-mails para TEST_EMAIL_RECIPIENT.
# False ---> ⚠️ MODO DE PRODUÇÃO REAL. E-mails são enviados aos clientes reais da Yampi.
MACRO_FORCE_TEST_EMAIL_RECIPIENT = False

# True  ---> Dispara simultaneamente uma cópia idêntica para TEST_EMAIL_RECIPIENT (supervisão).
# False ---> Desativa envio em duplicata.
MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = True

# True  ---> Salva arquivos .html gerados em local_data/emails/ para conferência visual.
# False ---> Não salva arquivos locais em disco.
MACRO_ENABLE_LOCAL_HTML_SAVING = False

# ------------------------------------------------------------------------------
# 2.2. Intervalos de Execução e Paginação dos Workers
# ------------------------------------------------------------------------------
MACRO_DAEMON_SLEEP_INTERVAL_SEG = 300     # Intervalo de repouso do daemon (5 minutos)
MACRO_W_ORDERS_INTERVAL = 30 * 60         # 30 minutos
MACRO_W_CARTS_INTERVAL = 30 * 60          # 30 minutos

MACRO_W_ORDERS_PAGE_LIMIT = 100           # Registros por página na API Yampi (Pedidos)
MACRO_W_ORDERS_PAGE_AMOUNT = 5            # Quantidade de páginas a buscar por ciclo
MACRO_W_CARTS_PAGE_LIMIT = 100            # Registros por página na API Yampi (Carrinhos)
MACRO_W_CARTS_PAGE_AMOUNT = 5             # Quantidade de páginas a buscar por ciclo
MACRO_DEBUG_LIMIT = 10                    # Limite de itens em rotinas de debug/teste

# ------------------------------------------------------------------------------
# 2.3. Resiliência do Servidor SMTP e Mascaramento de Logs
# ------------------------------------------------------------------------------
MACRO_SMTP_THROTTLE_DELAY_SEG = 2.0       # Tempo de espera (Rate Limit) entre cada envio SMTP
MACRO_SMTP_MAX_RETRIES = 3                # Máximo de tentativas de reenvio em caso de falha transitória
MACRO_SMTP_RETRY_BACKOFF_SEG = 5.0        # Fator multiplicador do backoff exponencial
MACRO_SMTP_TIMEOUT_SEG = 15               # Timeout de conexão e socket SMTP (segundos)
MACRO_DEFAULT_FALLBACK_FROM_EMAIL = "recuperacao@sualoja.com" # Remetente padrão caso omitido no .env
MACRO_EMAIL_MASK_VISIBLE_PREFIX_CHARS = 5 # Caracteres visíveis no início do e-mail ao logar

# ------------------------------------------------------------------------------
# 2.4. Dimensionamento do Pool de Conexões PostgreSQL
# ------------------------------------------------------------------------------
MACRO_PG_POOL_MIN_CONN = 1                # Conexões mínimas sempre ativas no pool
MACRO_PG_POOL_MAX_CONN = 20               # Conexões máximas simultâneas (concorrência dos workers)

# ------------------------------------------------------------------------------
# 2.5. Servidor de Webhooks (Meta WhatsApp API)
# ------------------------------------------------------------------------------
MACRO_META_WEBHOOK_VERIFY_TOKEN = "rodolfo_hulk_tasmania" # Token de verificação handshake da Meta
MACRO_WEBHOOK_SERVER_PORT = 5000                          # Porta local do servidor Flask de webhooks


# ==============================================================================
# SEÇÃO 3: CONSTANTES ESTÁTICAS E INFRAESTRUTURA PROFUNDA (RARA ALTERAÇÃO)
# ==============================================================================
# Parâmetros de base que garantem estabilidade de protocolo, fuso horário e integridade.

# ------------------------------------------------------------------------------
# 3.1. Fuso Horário e Integridade de Banco de Dados
# ------------------------------------------------------------------------------
MACRO_TIMEZONE_OFFSET_HOURS = 3           # Fuso horário padrão Brasil (UTC-3 / Brasília)
MACRO_DEFAULT_FALLBACK_CPF = "00000000000"# CPF padrão para campos NOT NULL caso ausente
MACRO_DEFAULT_FALLBACK_SKU = "N/A"        # SKU padrão para campos NOT NULL
MACRO_DEFAULT_FALLBACK_ORDER_NUMBER = "N/A"# Número de pedido padrão

# ------------------------------------------------------------------------------
# 3.2. Cliente HTTP da API Yampi
# ------------------------------------------------------------------------------
MACRO_YAMPI_BASE_URL = "https://api.dooki.com.br/v2" # Endpoint base oficial da Yampi
MACRO_HTTP_CONNECT_TIMEOUT = 5            # Timeout de conexão TCP (segundos)
MACRO_HTTP_READ_TIMEOUT = 15              # Timeout de leitura/resposta JSON (segundos)
MACRO_HTTP_MAX_RETRIES = 3                # Tentativas de retentativa em HTTP 429 ou 5xx
MACRO_HTTP_INITIAL_BACKOFF_SEG = 2.0      # Backoff inicial de espera pós-rate limit
MACRO_HTTP_MAX_BACKOFF_SEG = 60.0         # Teto máximo de espera em backoff (segundos)

# ------------------------------------------------------------------------------
# 3.3. Telemetria, Crash Report e Logs
# ------------------------------------------------------------------------------
MACRO_DEFAULT_LOG_PATH = "local_data/logs/app.log"    # Caminho do arquivo de logs principal
MACRO_CRASH_REPORT_MAX_BYTES = 10 * 1024 * 1024       # 10 MB (Limite de anexo no e-mail de crash)
MACRO_SENTRY_CRON_MONITOR_SLUG = "yampi-daemon-cycle" # Identificador do Cron Monitor no Sentry Cloud
