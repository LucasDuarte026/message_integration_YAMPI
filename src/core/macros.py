# Macros e Constantes de Negócio

# ==========================================
# Timers STG (Pedidos)
# ==========================================
MACRO_TIMEOUT_PAGAMENTO_SEG = 30 * 60     # 30 minutos em segundos (janela máxima inicial)
MACRO_DELAY_ORDER_PIX_EMAIL_SEG = 5 * 60  # 5 minutos em segundos (gordurinha/delay mínimo antes do Email 2)
MACRO_CUPOM_PEDIDO_1_HORAS = 12           # 24 horas
MACRO_CUPOM_PEDIDO_2_HORAS = 14        # 48 horas
MACRO_CUPOM_PEDIDO_3_HORAS = 16        # 72 horas
MACRO_PERDIDO_PEDIDO_HORAS = 18        # 96 horas

MACRO_STG_01_TIMER_02 = MACRO_TIMEOUT_PAGAMENTO_SEG
MACRO_STG_04_TIMER_05 = MACRO_CUPOM_PEDIDO_1_HORAS * 3600
MACRO_STG_05_TIMER_06 = MACRO_CUPOM_PEDIDO_2_HORAS * 3600
MACRO_STG_06_TIMER_07 = MACRO_CUPOM_PEDIDO_3_HORAS * 3600
MACRO_STG_07_TIMER_08 = MACRO_PERDIDO_PEDIDO_HORAS * 3600

# ==========================================
# Timers STC (Carrinhos)
# ==========================================
MACRO_CUPOM_CARRINHO_1_HORAS = 14       # 4 horas (lembrete 15)
MACRO_CUPOM_CARRINHO_2_HORAS = 16      # 24 horas (cupom 16)
MACRO_CUPOM_CARRINHO_3_HORAS = 18      # 48 horas (cupom 17)
MACRO_PERDIDO_CARRINHO_HORAS = 20      # 96 horas (carrinho perdido 18)

MACRO_MAX_CART_AGE_HOURS = 48           # Limite máximo em horas para desconsiderar carrinhos antigos

MACRO_STC_00_TIMER_15 = MACRO_CUPOM_CARRINHO_1_HORAS * 3600
MACRO_STC_15_TIMER_16 = MACRO_CUPOM_CARRINHO_2_HORAS * 3600
MACRO_STC_16_TIMER_17 = MACRO_CUPOM_CARRINHO_3_HORAS * 3600
MACRO_STC_17_TIMER_18 = MACRO_PERDIDO_CARRINHO_HORAS * 3600

# ==========================================
# Intervalos de Execução (Worker)
# ==========================================
MACRO_W_ORDERS_INTERVAL = 30 * 60    # 30 minutos
MACRO_W_CARTS_INTERVAL = 30 * 60     # 1 hora

# ==========================================
# Paginação e Limites da API
# ==========================================
MACRO_W_ORDERS_PAGE_LIMIT = 100
MACRO_W_ORDERS_PAGE_AMOUNT = 5
MACRO_W_CARTS_PAGE_LIMIT = 100
MACRO_W_CARTS_PAGE_AMOUNT = 5

# ==========================================
# Limite de Itens em Modo Debug / Cache
# ==========================================
MACRO_DEBUG_LIMIT = 10

# ==========================================
# Janela Máxima de Corte Precheck (Pedidos)
# ==========================================
MACRO_PRECHECK_ORDERS_MAX_DAYS = 15

# ==========================================
# Configurações Globais de Disparo e Testes
# ==========================================

# ------------------------------------------
# 1. Habilitação de Conexão e Disparo Real
# ------------------------------------------
# True  ---> Ativa o provedor SMTP/Meta real. O sistema vai conectar na rede e despachar os e-mails.
# False ---> Modo DRY-RUN (Simulação/Mock). Nenhum e-mail sai para a rede real; usa o DryRunMessageProvider.
MACRO_ENABLE_REAL_EMAIL_DISPATCH = True

# ------------------------------------------
# 2. Salvamento Local de Arquivos HTML
# ------------------------------------------
# True  ---> Gera e salva cada e-mail renderizado em arquivo .html em local_data/emails/ para conferência visual.
# False ---> Não salva arquivos HTML locais no disco durante o envio.
MACRO_ENABLE_LOCAL_HTML_SAVING = False 

# ------------------------------------------
# 3. Redirecionamento de Segurança de Destinatário
# ------------------------------------------
# True  ---> MODO DE SEGURANÇA / HOMOLOGAÇÃO. Todos os e-mails disparados são forçados e retratados para 
#            o seu e-mail de teste (configurado em TEST_EMAIL_RECIPIENT no .env). Nenhum cliente real recebe nada.
# False ---> ⚠️ MODO DE PRODUÇÃO REAL (PERIGO). Os e-mails serão enviados diretamente para os endereços 
#            REAIS dos clientes da loja obtidos via API da Yampi. Só altere para False com 100% de certeza!
MACRO_FORCE_TEST_EMAIL_RECIPIENT = False

# ------------------------------------------
# 4. Envio de Cópia em Duplicata (Supervisão em Produção)
# ------------------------------------------
# True  ---> ENVIO EM DUPLICATA ATIVADO. Toda vez que um e-mail for enviado para o cliente real da loja,
#            uma cópia idêntica será disparada simultaneamente para o e-mail de teste (TEST_EMAIL_RECIPIENT).
# False ---> ENVIO EM DUPLICATA DESATIVADO. E-mails são enviados exclusivamente para o destinatário primário.
MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = True
