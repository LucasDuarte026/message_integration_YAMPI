# Ports (Adaptadores Externos)

## Objetivo
Baseado nos conceitos de Hexagonal Architecture (Ports and Adapters), este diretório armazena as implementações concretas de serviços, plataformas ou APIs de **terceiros**. Todas as classes aqui devem obrigatoriamente herdar ou respeitar as Interfaces definidas em `src/domain/`.

## Arquivos e Responsabilidades
- **`message_provider.py`**: Implementa o provedor de mensageria da aplicação. Atualmente, possui a classe `DryRunMessageProvider` que serve como Mock para simular disparos no terminal sem gerar custos de API.
- **`postgres_repo.py`**: Implementa o `StateRepositoryProtocol` conectando-se a um banco de dados PostgreSQL. Utiliza um **Pool de Conexões Thread-Safe (`ThreadedConnectionPool` de 1 a 20 conexões)** com context manager dedicado (`_get_connection()`) para evitar saturação do DNS interno do Docker. Faz `upsert` das informações (pedidos e carrinhos), mantendo os estados atualizados (STG e STC) utilizando travas transacionais (`FOR UPDATE`) e instrumentado com spans do Sentry APM (`db.sql.query`). Registra atualizações sempre com base no fuso-horário correto (UTC-3 SP timezone-aware).
- **`smtp_email_provider.py`**: Implementa o `MessageProviderProtocol` conectando-se via SMTP para despachar as mensagens de e-mail. Este adaptador é **Stateful e Thread-Safe**, mantendo uma única conexão viva (Pooling), usando um `threading.Lock` para rate limiting (Throttle), repetições de envio com *Exponential Backoff* e **mascaramento de e-mails em logs** (preservando os 5 primeiros caracteres e o último antes do `@` para segurança e LGPD).

## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você criar um novo adaptador (ex: `ZenviaMessageProvider` ou `TwilioMessageProvider`) neste diretório, **DEVE** adicionar sua descrição, propósito e arquivo a este `README.md` no mesmo instante.

## Dependências
- **`src/domain/`**: Para implementar as interfaces exigidas pela arquitetura (ex: `MessageProviderProtocol`).
- **Externas**: `psycopg2-binary` (para PostgreSQL e pool), `sentry-sdk` (para tracing), `smtplib` e SDKs de mensageria externa.

## Future Updates (Pontos a serem modificados e melhorados)
- Substituir o uso do provedor Mock por adaptadores reais já construídos (como o `whatsapp_meta_provider.py`) em ambientes de produção.
- Adicionar suporte a *Health Checks* periódicos no `postgres_repo.py` para descartar conexões mortas no pool após longos períodos de inatividade.
- Monitoramento e Registro (Logs) aprofundados dentro dos adaptadores para capturar com clareza o motivo de rejeições ou falhas de provedores.
