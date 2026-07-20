# Diretório de Decisões de Projeto e Histórico de Implementação

**Data de Criação:** 2026-07-15  
**Última Atualização:** 2026-07-20  
**Versão:** 1.1.0  

Nesta pasta estão concentradas as diretrizes de mudanças locais, propostas de refatoração, decisões de arquitetura e histórico de evolução do sistema.

> [!NOTE]
> Estes documentos servem para manter o alinhamento de decisões locais de implementação e versionar o histórico de arquitetura do projeto.

---

## Índice de Documentos

1. [01_database_yampi_planning.md](file:///home/luska/Documents/projects/message_integration/project_decisions/01_database_yampi_planning.md)
   * **Assunto**: Definição da persistência em PostgreSQL e estrutura de tabelas para controle de estados de envio (Carrinhos Abandonados e Pedidos).
   * **Data**: 2026-07-15 (Atualizado: 2026-07-20)
   * **Status**: Aprovado.

2. [02_email_architecture.md](file:///home/luska/Documents/projects/message_integration/project_decisions/02_email_architecture.md)
   * **Assunto**: Especificação dos 5 fluxos transacionais de e-mail (Carrinho Abandonado 4h/24h/48h/72h e Pedidos Pago/Rastreio), modularidade e ambiente de testes.
   * **Data**: 2026-07-15 (Atualizado: 2026-07-20)
   * **Status**: Aprovado.

3. [03_mudanca_arquitetura_emails_e_geral.md](file:///home/luska/Documents/projects/message_integration/project_decisions/03_mudanca_arquitetura_emails_e_geral.md)
   * **Assunto**: Plano de refatoração completa do projeto, padronização da documentação interna, sistema de logs, tratamento de exceções e preparação para novas funcionalidades.
   * **Data**: 2026-07-20 (Atualizado: 2026-07-20)
   * **Status**: Em Desenvolvimento.
