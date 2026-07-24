# Future Implementations & Roadmap Técnico

Este documento rastreia débitos técnicos propositais, pendências de validação e funcionalidades deixadas para implementações futuras, servindo como guia de evolução do produto.

---

## 1. Validação de Parâmetros e Status da API Yampi (Pendências de Homologação)

- **Validação do Endpoint de Status (`GET /v2/{alias}/checkout/statuses`)**:
  Fazer chamada na conta da loja para confirmar os IDs e aliases exatos dos status secundários de pedidos:
  - `cancelled` (Pedido Cancelado/Perdido) → validar se `status_id = 6`.
  - `shipped` (Em transporte/Despachado) → validar se `status_id = 7`.
  - `delivered` (Entregue) → validar se `status_id = 9`.
  - `refunded` (Reembolsado) → validar se `status_id = 12`.
- **Payload Real de Despacho (`shipments`)**:
  Capturar amostra real de um pedido com status `shipped` para validar os nomes exatos das chaves `tracking_code` e `tracking_url` dentro de `shipments.data[0]`.

---

## 2. Réguas de Comunicação e Máquina de Estados (Refatoração v2.0.0+)

- **Status 95, 96, 97 (Detecção de Recompra via Pedido)**:
  - *Regra*: `90 + STG_anterior` ao identificar que um cliente com CPF + SKU já existente no banco realizou uma nova compra paga.
  - *Ação*: Disparo automático do "E-mail de Recompra" (agradecendo pela fidelidade e retorno).
- **Status 85, 86, 87 (Conversão de Carrinho Abandonado em Pedido)**:
  - *Regra*: `70 + STC_anterior` ao identificar que um carrinho abandonado que recebeu cupons se converteu em pedido.
  - *Ação*: Disparo do "E-mail de Agradecimento por Conversão de Carrinho".
- **Worker Autônomo de Varredura de Recompra**:
  - Worker em background para cruzamento estatístico periódico de `cpf`, `sku` e timestamps de pedidos, mapeando a frequência de recompra por cliente.
- **Conteúdo Específico e Cupons Dinâmicos**:
  - Inserção de cupons dinâmicos, códigos de desconto parametrizados e links de recuperação personalizados (`simulate_url`) diretamente nos templates de e-mail e WhatsApp.

---

## 3. Persistência de Dados, Performance e Concorrência

- **Locking Atômico "Adquire-Processa-Grava"**:
  - Implementar transações atômicas de curta duração (milissegundos) no PostgreSQL (`SELECT FOR UPDATE`), garantindo que chamadas lentas de rede (disparo SMTP) sejam feitas 100% **fora** de transações SQL ativas para não travar o banco.
- **Estudo de Gestão do Banco em Produção e Migrações DDL (`_init_db` vs `ALTER TABLE`)**:
  - *Contexto Atual*: A aplicação executa DDLs inline (`CREATE TABLE IF NOT EXISTS`, `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`) na inicialização do repositório (`_init_db`).
  - *Estudo Necessário para Produção*:
    - **Risco de Concorrência DDL no Startup**: Em ambiente de alta vazão com múltiplos pods/containers subindo simultaneamente, executar `ALTER TABLE` na inicialização do Python pode causar contenção de locks de catálogo (`AccessExclusiveLock`) no PostgreSQL.
    - **Evolução para Migrações Gerenciadas (ex: Alembic/Flyway)**: Avaliar a migração do DDL para uma ferramenta dedicada acionada na esteira de CI/CD ou em um job isolado de pré-deploy.
    - **Estratégia de Alterações Não-Destrutivas**: Garantir que inclusões de colunas `NOT NULL` novas (como `order_number`) sempre utilizem valores padrões (`DEFAULT 'N/A'`) ou rotinas de *backfill* assíncrono antes da aplicação rígida da constraint.
- **Purga e Arquivamento de Dados Históricos**:
  - Criar rotina no PostgreSQL para mover registros da `email_status_table` com mais de 365 dias para uma tabela de histórico (`email_status_archive`), mantendo o banco operacional enxuto e acelerando buscas O(1) por CPF/SKU.
- **Limpeza de Lotes Intermediários e Pastas Temporárias**:
  - Garantir a exclusão automática dos arquivos JSON de lotes de 100 itens das pastas `orders/` e `carts/` imediatamente após o consumo com sucesso pelo worker.
  - Em produção, após o envio do e-mail concluir com sucesso sem exceções, a pasta temporária individual de auditoria (`emails/cart_<cart_id>/`) deve ser removida automaticamente para otimizar armazenamento físico.

---

## 4. Orquestração, Webhooks e Mensageria (CPaaS)

- **Recepção de Webhooks Yampi em Tempo Real**:
  - Substituir/complementar o sistema de polling rotativo de 5 minutos por recepção ativa de Webhooks (`order.paid`, `order.status.updated`), disparando notificações em milissegundos via FastAPI/Flask.
- **Integração Fina de Webhooks do WhatsApp Meta**:
  - Persistir status de entrega (`read`, `delivered`, `failed`) recebidos no servidor Flask (`src/webhook_server.py`) diretamente no PostgreSQL (`db`), permitindo rastreabilidade do engajamento do cliente e atualizações em tempo real.
- **Cadeia de Resiliência e Fallback entre Canais**:
  - Caso o disparo por e-mail falhe ou retorne *bounce*, acionar automaticamente um canal alternativo (WhatsApp via Meta Cloud API ou SMS) configurado na porta de mensageria (`MessageProviderProtocol`).
- **Definição Final do Provedor CPaaS**:
  - Analisar a pesquisa do artefato de CPaaS e integrar a API vencedora utilizando o contrato `MessageProviderProtocol`.
