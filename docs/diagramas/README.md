# Diagramas de Estados da Aplicação

Este diretório contém os diagramas de estados (Mermaid) e documentação visual referentes às máquinas de estados duplas (STG e STC) do projeto **Message Integration**.

---

## 📂 Conteúdo do Diretório

| Arquivo | Descrição | Fluxo Mapeado |
| :--- | :--- | :--- |
| 📊 **[stateDiagramOrders.md](./stateDiagramOrders.md)** | Diagrama de estados para o ciclo de vida de **Pedidos (STG)**. | Confirmação de pagamento, lembrete PIX, janelas de cupons de recuperação (10%, 15%, 20%) e recompra. |
| 🛒 **[stateDiagramAbandonedCarts.md](./stateDiagramAbandonedCarts.md)** | Diagrama de estados para o ciclo de vida de **Carrinhos Abandonados (STC)**. | Transição de carrinhos sem pedido, cupons de recuperação (4, 5, 6 com `simulate_url`) e congelamento quando o carrinho vira pedido. |

---

## 🔗 Referência Técnica

A especificação completa das regras de transição, schema de banco de dados (`email_status_table`) e temporizadores pode ser consultada no documento principal:
- ⚙️ **[Especificação da Máquina de Estados](../email_state_machine.md)**
