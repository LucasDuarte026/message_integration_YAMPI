# Decisão 01: Planejamento de Banco de Dados e Integração Yampi

**Data de Criação:** 2026-07-15  
**Última Atualização:** 2026-07-20  
**Versão:** 1.0.0  
**Status:** Aprovado  
**Escopo:** Definição da camada de persistência e modelos de controle de envio.

---

## Visão Geral

Este documento define as diretrizes para a arquitetura da base de dados local, alinhadas à integração com a API da Yampi e à nova arquitetura de e-mails.

---

## 1. Carrinhos Abandonados (`cart_states`)

* **Proposta:** Tabela focada no controle de estados e timestamps de disparo de e-mails transacionais (Lembrete, Cupom 1, Cupom 2 e Abandono Final > 72h).
* **Decisão:** Aprovado. A base local não duplica dados cadastrais complexos, guardando apenas metadados de controle interno.

```sql
CREATE TABLE IF NOT EXISTS cart_states (
    cart_id VARCHAR(255) PRIMARY KEY,
    email_lembrete_sent_at TIMESTAMP,
    email_cupom1_sent_at TIMESTAMP,
    email_cupom2_sent_at TIMESTAMP,
    is_abandoned_72h BOOLEAN DEFAULT FALSE
);
```

---

## 2. Pedidos / Orders (`order_states`)

* **Proposta:** Tabela para controle dos envios após pagamento efetuado e código de rastreio disponibilizado.
* **Decisão:** A base local mantém estritamente os metadados de controle interno (saber se o e-mail 1 ou 2 já foi enviado). Dados cadastrais completos (valores, produtos e cliente) continuam sendo consultados em tempo real na API da Yampi.

```sql
CREATE TABLE IF NOT EXISTS order_states (
    order_id VARCHAR(255) PRIMARY KEY,
    email_pagamento_efetuado_sent_at TIMESTAMP,
    email_envio_rastreio_sent_at TIMESTAMP
);
```

---

## 3. Seleção do SGBD (Persistência)

* **Contexto:** Substituição da persistência legada baseada em arquivo SQLite local (`state.db`).
* **Decisão:** Migração obrigatória para **PostgreSQL** rodando via Docker, garantindo concorrência segura entre múltiplos workers e suporte a longo prazo.
