# Ports (Adaptadores Externos)

## Objetivo
Baseado nos conceitos de Hexagonal Architecture (Ports and Adapters), este diretório armazena as implementações concretas de serviços, plataformas ou APIs de **terceiros**. Todas as classes aqui devem obrigatoriamente herdar ou respeitar as Interfaces definidas em `src/domain/`.

## Arquivos e Responsabilidades
- **`message_provider.py`**: Implementa o provedor de mensageria da aplicação. Atualmente, possui a classe `DryRunMessageProvider` que serve como Mock para simular disparos no terminal sem gerar custos de API.

## 🚨 Diretiva de Manutenção (Para IA)
> [!IMPORTANT]
> Se você criar um novo adaptador (ex: `ZenviaMessageProvider` ou `TwilioMessageProvider`) neste diretório, **DEVE** adicionar sua descrição, propósito e arquivo a este `README.md` no mesmo instante.
