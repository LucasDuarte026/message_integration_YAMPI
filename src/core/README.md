# Core (Infraestrutura Base)

## Objetivo
O diretório `core` abriga os componentes básicos de infraestrutura interna que suportam a aplicação. São os componentes que lidam com estado interno, configurações e nossa própria fonte de dados primária (API Yampi).

## Arquivos e Responsabilidades
- **`config.py`**: Gerenciador centralizado de variáveis de ambiente e credenciais. Garante a segurança retirando dados sensíveis do restante do código.
- **`client.py`**: O cliente robusto `YampiClient`. Implementa as requisições HTTP, paginação, fallback, rate limits e autenticação para consumir a API da Yampi. Instrumentado com spans do Sentry APM (`http.client`) para medição de latência das chamadas de rede.
- **`db.py`**: Implementação concreta em SQLite do repositório de persistência (`StateRepositoryProtocol`). Serve para salvar o estado da aplicação em modo local/standalone.
- **`logging_config.py`**: Configuração central de telemetria e logs. Inicializa o Sentry SDK (com taxa de amostragem `TRACES_SAMPLE_RATE` configurável e `send_default_pii=False` para LGPD), além dos interceptadores globais de crash (`sys.excepthook` e `threading.excepthook`) com disparo de e-mail SMTP de emergência.
- **`macros.py`**: Arquivo de configurações de constantes e macros de negócios. Define *timers* para STG (Pedidos) e STC (Carrinhos), limites, paginação, e intervalos de workers e daemon:
  - `MACRO_DAEMON_SLEEP_INTERVAL_SEG`: Intervalo de ciclo do daemon (padrão: 300 segundos / 5 minutos).
  - `MACRO_SMTP_THROTTLE_DELAY_SEG`, `MACRO_SMTP_MAX_RETRIES`, `MACRO_SMTP_RETRY_BACKOFF_SEG`: Controle estrito de throttling e resiliência das conexões SMTP contra bans.
  - `MACRO_ENABLE_REAL_EMAIL_DISPATCH`: Habilita ou desabilita o disparo real aos provedores SMTP/API.
  - `MACRO_FORCE_TEST_EMAIL_RECIPIENT`: Força o redirecionamento de todos os e-mails para um único e-mail de teste (`TEST_EMAIL_RECIPIENT`) sem impactar clientes reais.
  - `MACRO_ENABLE_LOCAL_HTML_SAVING`: Habilita ou desabilita a geração local de e-mails em HTML (útil para debug e fallback).
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
