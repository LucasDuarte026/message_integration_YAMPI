# Ports (Adaptadores Externos)

## Objetivo
Baseado nos conceitos de Hexagonal Architecture (Ports and Adapters), este diretório armazena as implementações concretas de serviços, plataformas ou APIs de **terceiros**. Todas as classes aqui devem obrigatoriamente herdar ou respeitar as Interfaces definidas em `src/domain/`.

## Arquivos e Responsabilidades
- **`message_provider.py`**: Implementa o provedor de mensageria da aplicação. Atualmente, possui a classe `DryRunMessageProvider` que serve como Mock para simular disparos no terminal sem gerar custos de API.
- **`postgres_repo.py`**: Implementa o `StateRepositoryProtocol` conectando-se a um banco de dados PostgreSQL. Utiliza um **Pool de Conexões Thread-Safe (`ThreadedConnectionPool` de 1 a 20 conexões)** com context manager dedicado (`_get_connection()`) para evitar saturação do DNS interno do Docker. Faz `upsert` das informações (pedidos e carrinhos) protegendo `data_pedido` e `data_carrinho` contra regressão temporal com `COALESCE(LEAST(...))`, mantendo os estados atualizados (STG e STC) utilizando travas transacionais (`FOR UPDATE`) e instrumentado com spans do Sentry APM (`db.sql.query`). Registra todas as datas e atualizações estritamente no padrão **UTC-First**.
- **`smtp_email_provider.py`**: Implementa o `MessageProviderProtocol` conectando-se via SMTP para despachar as mensagens de e-mail usando a API moderna `email.message.EmailMessage` (Python 3.12). Suporta roteamento dual de conta SMTP (`oficial@` para avisos transacionais e `promo_user`/`comercial@` opcional para disparos promocionais), injeta cabeçalhos obrigatórios RFC 5322 (`Message-ID`, `Date`, `From` com nome amigável e `Reply-To`), cabeçalhos RFC 8058 (`List-Unsubscribe` e `List-Unsubscribe-Post: List-Unsubscribe=One-Click`) em fluxos promocionais, árvore MIME `text/plain` seguida de `text/html` (RFC 2046), suporte a imagens locais inline (`image/webp`, etc.) resolvidas de forma modular via `assets_dir` (`EMAIL_ASSETS_DIR`, com degradação graciosa caso a pasta não exista no repositório open source) e zero anexo quando forem URLs HTTPS externas. Mantém conexões vivas (Stateful/Pooling) encerradas ao fim do ciclo via `close()`, `threading.Lock` para rate limiting, retry com *Exponential Backoff*, validação explícita de destinatários recusados (`refused`) retornados por `sendmail()` convertida em `SMTPRecipientsRefused` com endereço mascarado e mascaramento de e-mails em logs para LGPD. Emite métricas Sentry (`email.dispatch.started`, `email.dispatch.sent` antes do *throttling* e `email.dispatch.failed`), abre span `email.smtp.send` por tentativa via `start_smtp_span()`, registra breadcrumbs `smtp.retry` e captura falhas definitivas/fatais preservando *traceback* completo, `retry_history` e contexto `smtp_dispatch` sem duplicação de *issues* com a `LoggingIntegration` (`DedupeIntegration`).

## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você criar um novo adaptador (ex: `ZenviaMessageProvider` ou `TwilioMessageProvider`) neste diretório, **DEVE** adicionar sua descrição, propósito e arquivo a este `README.md` no mesmo instante.

## Dependências
- **`src/domain/`**: Para implementar as interfaces exigidas pela arquitetura (ex: `MessageProviderProtocol`).
- **Externas**: `psycopg2-binary` (para PostgreSQL e pool), `sentry-sdk` (para tracing), `smtplib` e SDKs de mensageria externa.

## Future Updates (Pontos a serem modificados e melhorados)
- Adicionar adaptador real de WhatsApp (ex.: `whatsapp_meta_provider.py`) implementando `MessageProviderProtocol` para disparo ativo além do e-mail SMTP.
- Adicionar suporte a *Health Checks* periódicos no `postgres_repo.py` para descartar conexões mortas no pool após longos períodos de inatividade.
- Monitoramento e Registro (Logs) aprofundados dentro dos adaptadores para capturar com clareza o motivo de rejeições ou falhas de provedores.
