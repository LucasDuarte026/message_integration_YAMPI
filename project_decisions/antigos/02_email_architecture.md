# Decisão 02: Arquitetura de Comunicação e Fila de E-mails

**Data de Criação:** 2026-07-15  
**Última Atualização:** 2026-07-20  
**Versão:** 1.0.0  
**Status:** Aprovado  
**Escopo:** Mapeamento dos fluxos de disparo transacional, modularidade de templates e regras de homologação.

---

## Visão Geral

Este documento detalha o funcionamento de alto nível da integração de mensagens e e-mails, especificando a modulação por casos de uso, tratamento de exceções, estrutura de pastas para templates e comportamento do ambiente de testes.

---

## 1. Diretrizes de Arquitetura e Rastreabilidade

* **Documentação Descentralizada**: Questões pendentes ou prazos específicos de negócio (ex: número de dias úteis para envio do rastreio) devem ser documentados no `README.md` do respectivo módulo para manter o alinhamento capilarizado.
* **Modularidade e Logs**: O sistema deve possuir isolamento de responsabilidades, logs estruturados e tratamento rigoroso de exceções para evitar perda de estado durante disparos.

---

## 2. Cenários de Disparo Transacional

Os disparos são divididos em 5 tipos de e-mail principais:

### Cenário A: Fluxo de Pedidos Concluídos

1. **E-mail 1 (Confirmação de Pagamento)**:
   * **Gatilho**: O cliente finaliza a compra e a Yampi confirma o pagamento (geração do `order_id`).
   * **Ação**: Envia e-mail de confirmação com dados da compra e avisa que o código de rastreio será enviado assim que for despachado.
   * **Registro**: Salva a marcação no banco PostgreSQL (`order_states.email_pagamento_efetuado_sent_at`).

2. **E-mail 2 (Envio de Rastreio)**:
   * **Gatilho**: Acompanhamento da API da Yampi detecta mudança de status para "em transporte".
   * **Ação**: Dispara e-mail contendo o código e link de rastreamento.
   * **Registro**: Salva no banco PostgreSQL (`order_states.email_envio_rastreio_sent_at`) e finaliza a esteira deste pedido.

### Cenário B: Fluxo de Carrinhos Abandonados

1. **E-mail 3 (Lembrete - 4 horas)**:
   * **Gatilho**: Carrinho aberto sem conversão após 4 horas.
   * **Ação**: Envia lembrete amigável incentivando a conclusão da compra.

2. **E-mail 4 (Cupom 1 - 24 horas)**:
   * **Gatilho**: Permanência do status de abandono por 24 horas.
   * **Ação**: Dispara e-mail com cupom de desconto de 10%.

3. **E-mail 5 (Cupom 2 - 48 horas)**:
   * **Gatilho**: Permanência do status de abandono por 48 horas.
   * **Ação**: Dispara e-mail com cupom de desconto de 20%.

4. **Finalização (72 horas)**:
   * **Gatilho**: Transcorridas 72 horas sem conclusão.
   * **Ação**: Marca no banco PostgreSQL (`cart_states.is_abandoned_72h = TRUE`) encerrando o ciclo de tentativas.

---

## 3. Estrutura da Base de Dados Dupla

O controle local de persistência é dividido em duas frentes com responsabilidades distintas:
* **`cart_states`**: Rastreia ciclo de vida e e-mails de carrinhos abandonados.
* **`order_states`**: Rastreia etapas de liquidação e pós-venda dos pedidos.

---

## 4. Ambiente de Testes e Modo Homologação (Dry-Run)

> [!IMPORTANT]
> **Modo Provisório de Segurança:** Durante a fase de homologação e desenvolvimento, **todos os disparos de e-mail são redirecionados exclusivamente para a caixa de testes configurada** (`deutschlucas026@gmail.com`), impedindo qualquer disparo acidental para e-mails de clientes reais da Yampi até a entrada oficial em produção.