# Macros e Constantes de Negócio

# ==========================================
# Timers STG (Pedidos) - em segundos
# ==========================================
MACRO_STG_01_TIMER_02 = 30 * 60      # 30 minutos (Null -> 1, Null -> 2, Null -> 4, 2 -> 4)
MACRO_STG_04_TIMER_05 = 24 * 60 * 60 # 24 horas (4 -> 5)
MACRO_STG_05_TIMER_06 = 48 * 60 * 60 # 48 horas (5 -> 6)
MACRO_STG_06_TIMER_07 = 72 * 60 * 60 # 72 horas (6 -> 7)
MACRO_STG_07_TIMER_08 = 96 * 60 * 60 # 96 horas (7 -> 8)

# ==========================================
# Timers STC (Carrinhos) - em segundos
# ==========================================
MACRO_STC_00_TIMER_15 = 4 * 60 * 60  # 4 horas (Null -> 15)
MACRO_STC_15_TIMER_16 = 24 * 60 * 60 # 24 horas (15 -> 16)
MACRO_STC_16_TIMER_17 = 48 * 60 * 60 # 48 horas (16 -> 17)
MACRO_STC_17_TIMER_18 = 96 * 60 * 60 # 96 horas (17 -> 18)

# ==========================================
# Intervalos de Execução (Worker)
# ==========================================
MACRO_W_ORDERS_INTERVAL = 30 * 60    # 30 minutos
MACRO_W_CARTS_INTERVAL = 60 * 60     # 1 hora

# ==========================================
# Paginação e Limites da API
# ==========================================
MACRO_W_ORDERS_PAGE_LIMIT = 100
MACRO_W_ORDERS_PAGE_AMOUNT = 5
MACRO_W_CARTS_PAGE_LIMIT = 100
MACRO_W_CARTS_PAGE_AMOUNT = 5
