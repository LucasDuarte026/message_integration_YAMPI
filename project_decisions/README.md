# Diretório de Decisões de Projeto e Histórico de Implementação

**Data de Criação:** 2026-07-15  
**Última Atualização:** 2026-07-21  
**Versão:** 1.2.0  

Nesta pasta estão concentradas as diretrizes de mudanças locais, propostas de refatoração, decisões de arquitetura e histórico de evolução do sistema.

> [!NOTE]
> Estes documentos servem para manter o alinhamento de decisões locais de implementação e versionar o histórico de arquitetura do projeto.

---

## Índice de Documentos

1. [01_database_yampi_planning.md](./01_database_yampi_planning.md)
   * **Assunto**: Definição da persistência em PostgreSQL e estrutura de tabelas para controle de estados de envio (Carrinhos Abandonados e Pedidos).
   * **Data**: 2026-07-15 (Atualizado: 2026-07-20)
   * **Status**: Aprovado.

2. [02_email_architecture.md](./02_email_architecture.md)
   * **Assunto**: Especificação dos 5 fluxos transacionais de e-mail (Carrinho Abandonado 4h/24h/48h/72h e Pedidos Pago/Rastreio), modularidade e ambiente de testes.
   * **Data**: 2026-07-15 (Atualizado: 2026-07-20)
   * **Status**: Aprovado.

3. [03_mudanca_arquitetura_emails_e_geral.md](./03_mudanca_arquitetura_emails_e_geral.md)
   * **Assunto**: Plano de refatoração completa do projeto, padronização da documentação interna, sistema de logs, tratamento de exceções e preparação para novas funcionalidades.
   * **Data**: 2026-07-20 (Atualizado: 2026-07-20)
   * **Status**: Em Desenvolvimento / Base da Versão 2.0.0.

4. [04_refactor_logic_emails.md](./antigos/04_refactor_logic_emails.md)
   * **Assunto**: Especificação formal da máquina de estados (STG/STC), schema unificado `email_status_table`, contratos de workers e macros para a versão 2.0.0.
   * **Data**: 2026-07-21
   * **Status**: Aprovado (Especificação pronta para implementação da v2.0.0).
   * **Diagramas**:
     - [stateDiagramOrders.md](../docs/diagramas/stateDiagramOrders.md) (Fluxo STG - Pedidos)
     - [stateDiagramAbandonedCarts.md](../docs/diagramas/stateDiagramAbandonedCarts.md) (Fluxo STC - Carrinhos Abandonados)
     - [Índice de Diagramas](../docs/diagramas/README.md)

5. [05_email_refactor.md](./Emails_design_upgrade/05_email_refactor.md)
   * **Assunto**: Refatoração completa dos e-mails usando MJML, nomenclatura desacoplada (Cupons 1-3 pedidos, Cupons 4-6 carrinho), auto-injeção de imagens e `brand_data.yml` como Fonte Zero de Informações.
   * **Data**: 2026-07-27
   * **Status**: Aprovado e Implementado.

6. [06_products_table.md](./06_products_table.md)
   * **Assunto**: Especificação e renderização da tabela de produtos nos e-mails transacionais (extração direta de itens, frete e total, alinhamento por colunas e design system).
   * **Data**: 2026-07-27
   * **Status**: Aprovado e Implementado (v4.1.0).



