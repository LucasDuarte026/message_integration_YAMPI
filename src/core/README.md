# Core (Infraestrutura Base)

## Objetivo
O diretório `core` abriga os componentes básicos de infraestrutura interna que suportam a aplicação. São os componentes que lidam com estado interno, configurações e nossa própria fonte de dados primária (API Yampi).

## Arquivos e Responsabilidades
- **`config.py`**: Gerenciador centralizado de variáveis de ambiente e credenciais. Garante a segurança retirando dados sensíveis do restante do código.
- **`client.py`**: O cliente robusto `YampiClient`. Implementa as requisições HTTP, paginação, fallback, rate limits e autenticação para consumir a API da Yampi. Instrumentado com spans do Sentry APM (`http.client`) para medição de latência das chamadas de rede.
- **`db.py`**: Implementação concreta em SQLite do repositório de persistência (`StateRepositoryProtocol`). Serve para salvar o estado da aplicação em modo local/standalone.
- **`logging_config.py`**: Configuração central de telemetria e logs. Inicializa o Sentry SDK (com taxa de amostragem `TRACES_SAMPLE_RATE` configurável e `send_default_pii=False` para LGPD), além dos interceptadores globais de crash (`sys.excepthook` e `threading.excepthook`) com disparo de e-mail SMTP de emergência.
- **`macros.py`**: Arquivo visual e modular de configurações, constantes e macros de negócios dividido em 3 setores:
  - **Seção 1 (Planos de Horários e Timers de Cupons):** Timers das réguas de relacionamento de e-mails (`STG` para Pedidos e `STC` para Carrinhos), janelas de cupons e pre-check cutoff.
  - **Seção 2 (Configurações Médias de Operação e Workers):** Flags de disparo (`MACRO_ENABLE_REAL_EMAIL_DISPATCH`, etc.), intervalos de workers e do daemon (`MACRO_DAEMON_SLEEP_INTERVAL_SEG`), parâmetros de SMTP/Rate Limit e dimensionamento do pool PostgreSQL (`MACRO_PG_POOL_MIN_CONN` e `MACRO_PG_POOL_MAX_CONN`).
  - **Seção 3 (Constantes Estáticas e Infraestrutura Profunda):** Timezone offset (UTC-3), fallbacks de integridade SQL, timeouts da API Yampi (`MACRO_YAMPI_BASE_URL`, connect/read timeouts) e telemetria.
- **`time_utils.py`**: Módulo utilitário de tempo. Define funções como `get_now_sp()` e `make_aware_sp()` para manipulação segura e padronizada de datas no fuso horário de São Paulo (UTC-3), prevenindo *double-shifting* no banco de dados e nos arquivos de log.
## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você modificar, adicionar ou remover qualquer arquivo de infraestrutura neste diretório, **DEVE** atualizar este arquivo `README.md` imediatamente para refletir essas mudanças arquiteturais.

## Dependências
- **Nenhuma no Nível de Regras de Negócio**: O `core` não depende de workers ou ports (embora instancie a conexão HTTP que as interfaces definem).
- **Externas**: Bibliotecas como `requests` para requisições HTTP, biblioteca nativa do `sqlite3`, `sentry-sdk` para telemetria e gerência de variáveis de ambiente.

## Future Updates (Pontos a serem modificados e melhorados)
- Expandir o `client.py` para suportar *Retries* com decorators ou Circuit Breaker caso a API da Yampi passe por instabilidades prolongadas.
- Adicionar validações mais robustas no `config.py` (usando Pydantic) no carregamento das variáveis de ambiente.
