# Decisão 06: Renderização da Tabela de Produtos nos E-mails

**Data de Criação:** 2026-07-27  
**Última Atualização:** 2026-07-27  
**Versão:** 4.1.0  
**Status:** Aprovado  
**Escopo:** Definição da estratégia de extração de itens, alinhamento de colunas, frete, valor total e regras de design da tabela de produtos nos e-mails transacionais.

---

## Visão Geral

Este documento estabelece a especificação técnica e visual definitiva para a exibição do resumo de produtos comprados (ou deixados no carrinho) em mensagens transacionais. O objetivo é dar total transparência visual dos itens, quantidades, frete e valor total pago, seguindo o **Eleveme Email UI Design System**.

---

## 1. Contexto e Decisão Arquitetural

* **Escopo Restrito a E-mails Transacionais do Pedido/Carrinho:**
  - A tabela de produtos é exibida exclusivamente nos e-mails de **Pedidos** (`pedido_aprovado`, `pedido_pendente`, `pedido_a_caminho`) e **Carrinhos Abandonados** (`carrinho_abandonado_cupom4`, `carrinho_abandonado_cupom5`, `carrinho_abandonado_cupom6`).
  - **Exclusão Proposital**: Os e-mails de cupons de incentivo pós-compra (`cupom_pedido_1`, `cupom_pedido_2`, `cupom_pedido_3`) **não exibem a tabela**, pois são e-mails promocionais focados na próxima compra do cliente.

* **Sem Imagens de Produtos:** A tabela é mantida estritamente textual para maximizar a entregabilidade (inbox rate) e evitar bloqueio de assets externos pelos clientes de e-mail.
* **Formatos das Colunas:** A tabela possui 3 colunas principais:
  1. `Item`: Título do produto, "Frete" ou "Total do Pedido" (alinhado à esquerda).
  2. `Quantidade`: Quantidade de unidades compradas ou hífen `-` para linhas de totais (centralizado).
  3. `Preço`: Valor unitário do item, valor do frete e valor total pago (alinhado à direita).

---

## 2. Padrões de Design e Cores (Design System)

Conforme os padrões do [design_system.md](./antigos/emails_design_upgrade/design_system.md):

* **Fonte Universal:** `arial, 'helvetica neue', helvetica, sans-serif` para compatibilidade total (Gmail, iOS Mail, Outlook).
* **Cabeçalhos de Coluna:** `<th style="padding: 10px; font-family: sans-serif; font-size: 13px; color: #475569;">` com o texto `Quantidade` (não abreviado como Qtd).
* **Linhas de Itens:** Texto `#334155` (Slate 700) com peso `700` para destaque do produto.
* **Linha de Frete:** Sempre visível (exibindo valor real ou `R$ 0.00` em caso de frete grátis), rotulado sob a coluna `Item`, com cor `#64748B` (Slate 500) e tamanho `13px`.
* **Linha de Total do Pedido:** Fundo `#E2E8F0` (Slate 200), texto e valores destacados com a cor primária da marca `#1E3A8A` (Deep Blue) e peso `700`.

---

## 3. Estrutura HTML Padrão Renderizada

```html
<table width="100%" style="border-collapse: collapse; background-color: #F8FAFC; border-radius: 8px; overflow: hidden;">
  <thead>
    <tr style="background-color: #E2E8F0; text-align: left;">
      <th style="padding: 10px; font-family: sans-serif; font-size: 13px; color: #475569;">Item</th>
      <th style="padding: 10px; font-family: sans-serif; font-size: 13px; color: #475569; text-align: center;">Quantidade</th>
      <th style="padding: 10px; font-family: sans-serif; font-size: 13px; color: #475569; text-align: right;">Preço</th>
    </tr>
  </thead>
  <tbody>
    <!-- Linhas dos Produtos -->
    <tr style="border-bottom: 1px solid #e2e8f0;">
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700;">{title}</td>
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #475569; text-align: center;">{qty}</td>
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #334155; font-weight: 700; text-align: right;">R$ {price}</td>
    </tr>
    <!-- Linha do Frete (Sempre Presente) -->
    <tr style="border-bottom: 1px solid #e2e8f0; color: #64748b;">
      <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px;">Frete</td>
      <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px; text-align: center;">-</td>
      <td style="padding: 10px 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 13px; text-align: right;">R$ {ship_cost}</td>
    </tr>
    <!-- Linha de Total do Pedido -->
    <tr style="background-color: #e2e8f0; font-weight: 700;">
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a;">Total do Pedido</td>
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a; text-align: center;">-</td>
      <td style="padding: 12px; font-family: arial, 'helvetica neue', helvetica, sans-serif; font-size: 14px; color: #1e3a8a; text-align: right;">R$ {value_total}</td>
    </tr>
  </tbody>
</table>
```

---

## 4. Arquivos Alterados e Componentes Envolvidos

1. **`src/services/email_builders/base_builder.py`**:
   - Método `_build_items_html` atualizado para extrair nomes e preços promocionais da Yampi (`sku.data.title`, `sku.data.price_discount`), além de suportar tanto payloads de **Orders** (`value_shipment`, `value_total`) quanto de **Carrinhos Abandonados** (`totalizers.shipment`, `totalizers.total` / `totalizers.subtotal`).
   - Adiciona automaticamente as linhas de frete (sempre visível) e a linha de valor total alinhadas pelas colunas.
2. **Templates de E-mail (`src/templates/emails/` e `src/templates/emails/mjml_src/`)**:
   - **E-mails de Pedidos**: `pedido_aprovado.html`, `pedido_a_caminho.html`, `pedido_pendente.html` (cabeçalho padronizado como `Quantidade`).
   - **E-mails de Carrinho Abandonado**: `carrinho_abandonado_cupom4` (.html e .mjml), `carrinho_abandonado_cupom5` (.html e .mjml), `carrinho_abandonado_cupom6` (.html e .mjml) atualizados com o bloco `{% if items_html %}` contendo a estrutura de tabela.
   - **Exclusão de Cupons de Pedido**: `cupom_pedido_1`, `cupom_pedido_2`, `cupom_pedido_3` mantidos sem tabela por serem e-mails promocionais pós-compra.
3. **Suíte de Testes `tests/`**:
   - `test_orders.py` e `test_abandoned_cart.py`: Cobertura automatizada para renderização da tabela a partir de dados reais de mock (`orders_mock.json` e `carts_mock.json`).
   - HTMLs de teste gerados para verificação visual: `tests/pedido_aprovado_teste.html`, `tests/carrinho_cupom4_teste.html`, `tests/carrinho_cupom5_teste.html` e `tests/carrinho_cupom6_teste.html`.

