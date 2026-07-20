# Ports (Adaptadores Externos)

## Objetivo
Baseado nos conceitos de Hexagonal Architecture (Ports and Adapters), este diretório armazena as implementações concretas de serviços, plataformas ou APIs de **terceiros**. Todas as classes aqui devem obrigatoriamente herdar ou respeitar as Interfaces definidas em `src/domain/`.

## Arquivos e Responsabilidades
- **`message_provider.py`**: Implementa o provedor de mensageria da aplicação. Atualmente, possui a classe `DryRunMessageProvider` que serve como Mock para simular disparos no terminal sem gerar custos de API.

## 🚨 Diretiva de Manutenção (Para IA)
> [!IMPORTANT]
> Se você criar um novo adaptador (ex: `ZenviaMessageProvider` ou `TwilioMessageProvider`) neste diretório, **DEVE** adicionar sua descrição, propósito e arquivo a este `README.md` no mesmo instante.

## Dependências
- **`src/domain/`**: Para implementar as interfaces exigidas pela arquitetura (ex: `MessageProviderProtocol`).
- **Externas**: SDKs de terceiros ou bibliotecas HTTP para integração externa (ex: Bibliotecas oficiais da Meta para WhatsApp, ou `smtplib` para e-mail).

## Future Updates (Pontos a serem modificados e melhorados)
- Substituir o uso do provedor Mock por adaptadores reais já construídos (como o `whatsapp_meta_provider.py`) em ambientes de produção.
- Adicionar validação de payload estrita nos adaptadores de mensageria para garantir que as mensagens respeitam os templates aprovados antes mesmo do disparo de rede.
- Monitoramento e Registro (Logs) aprofundados dentro dos adaptadores para capturar com clareza o motivo de rejeições ou falhas de provedores.
