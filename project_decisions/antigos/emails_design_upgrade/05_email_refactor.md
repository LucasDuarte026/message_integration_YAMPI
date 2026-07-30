# Decisão 05: Upgrade de Design e Arquitetura de E-mails

**Data de Criação:** 2026-07-27  
**Última Atualização:** 2026-07-27  
**Versão:** 1.0.0  
**Status:** Concluído  
**Escopo:** Modernização visual e arquitetural da geração de e-mails transacionais e de marketing, substituindo manipulação manual de strings por um motor robusto de templates e design responsivo.

---

## Visão Geral

Este documento registra as decisões tomadas para refatorar o processo de montagem e envio dos e-mails da aplicação (Carrinho Abandonado e Pedidos). O objetivo é garantir segurança (prevenção de XSS), qualidade de renderização (em todos os clientes de e-mail, incluindo Outlook) e centralização de dados e copy.

---

## 1. Infraestrutura e Motor de Templates

* **Proposta:** Substituir a injeção manual de dados (`html_body.replace("{name}", name)`) no `base_builder.py` por uma ferramenta profissional.
* **Decisão:** Aprovado o uso do **Jinja2**. Ele fornece autoescape nativo (protegendo contra XSS, especialmente nas variáveis de clientes e produtos) e permite utilizar estruturas lógicas (`{% for %}`, `{% if %}`) dentro do HTML.

---

## 2. Framework de Design Responsivo

* **Proposta:** Parar de codar e-mails escrevendo tabelas de HTML puro "do zero", pois quebram frequentemente dependendo do provedor do destinatário.
* **Decisão:** Aprovado o uso do **MJML**. Os layouts serão criados usando os componentes do MJML (como `<mj-button>`) e em seguida compilados para o HTML estático que o Jinja2 utilizará. Isso garantirá um design impecável independentemente do dispositivo ou cliente de e-mail.

---

## 3. Mock Generator (Sandbox Visual)

* **Proposta:** Criar um ambiente para teste e visualização rápida dos e-mails.
* **Decisão:** Aprovado. Será criado o script utilitário `src/scripts/email_mock_generator.py`. Ele irá injetar "dados mockados" (ex: pedidos falsos, nomes controlados) nos templates e gerar arquivos estáticos que poderão ser abertos no navegador. Isso blindará a arquitetura, permitindo testes de layout sem precisar rodar um webhook de teste vindo da Yampi ou alterar o banco de dados.

---

## 4. Centralização de Informações (Fonte Oficial de Dados)

* **Proposta:** Evitar que dados de contato e informações de branding fiquem *hardcoded* espalhados pelos diversos templates HTML.
* **Decisão:** Aprovado. O arquivo `src/templates/emails/brand_data.yml` é a **fonte oficial e centralizada de verdade** para todos os e-mails. Ele atua como macro central para:
  - Textos institucionais, Slogans e Copywriting dos templates
  - CNPJ, Horários de Atendimento e Disclaimers
  - Canais de Suporte (WhatsApp e E-mail de Atendimento)
  - Links Oficiais das Redes Sociais (Instagram, Facebook) e Cores do Design System

---

## 5. Workflow de Copywriting e Design

* **Proposta:** Delegar as decisões de layout e gatilhos mentais para as skills/agentes especialistas em conversão ao invés de codificá-las rigidamente de início.
* **Decisão:** Aprovado. A estruturação inicial usará as imagens de referência (`ref1/`), mas os copys de urgência/escassez para os e-mails de cupons (10%, 15%, 20%) serão definidos interativamente usando os agentes `agency-ad-creative-strategist` e `agency-ui-designer`. O SMTP Hostinger da loja continuará sendo o responsável final pelo disparo.

---

## 6. Referência Visual e Estilo (.eml)

* **Proposta:** Adotar padrões estéticos comprovados em e-mails internacionais de alta conversão.
* **Decisão:** Incorporado o estilo do e-mail de referência (`Up to 40% off your next island escape.eml`):
  - **Tipografia Universal**: `arial, 'helvetica neue', helvetica, sans-serif` para máxima legibilidade e compatibilidade perfeita em todos os leitores de e-mail (incluindo o Outlook).
  - **Botões Pill-Shape**: Botões arredondados (`border-radius: 28px`) com sombras suaves (`box-shadow`).
  - **Ferryhopper Card Box**: Bloco cinza contínuo (`#F1F5F9` com `border-radius: 16px`) com a imagem central tocando as bordas superiores do card (`padding="0"`).

---

## 7. Inventário de Templates Desenvolvidos

Todos os e-mails foram construídos em MJML (`src/templates/emails/mjml_src/`), compilados para HTML Jinja2 (`src/templates/emails/`) e validados visualmente no gerador de mocks (`src/templates/emails/mocks/`):

### 7.1 Eixo STG (Pedidos)
1. **Email 1 — Pedido Aprovado**: `pedido_aprovado.mjml` $\to$ `mock_pedido_aprovado.html` (*STG 1*)
2. **Email 2 — Pedido Pendente / Incentivo ao Pagamento**: `pedido_pendente.mjml` $\to$ `mock_pedido_pendente.html` (*STG 2*)
3. **Email 3 — Pedido a Caminho / Rastreio**: `pedido_a_caminho.mjml` $\to$ `mock_pedido_a_caminho.html` (*STG 3*)
4. **Cupom 1 — Recuperação de Pedido**: `cupom_pedido_1.mjml` $\to$ `mock_cupom_pedido_1.html` (*STG 5*)
5. **Cupom 2 — Recuperação de Pedido**: `cupom_pedido_2.mjml` $\to$ `mock_cupom_pedido_2.html` (*STG 6*)
6. **Cupom 3 — Recuperação de Pedido**: `cupom_pedido_3.mjml` $\to$ `mock_cupom_pedido_3.html` (*STG 7*)

### 7.2 Eixo STC (Carrinhos Abandonados)
7. **Cupom 4 — Carrinho Abandonado 1**: `carrinho_abandonado_cupom4.mjml` $\to$ `mock_carrinho_abandonado_cupom4.html` (*STC 15*)
8. **Cupom 5 — Carrinho Abandonado 2**: `carrinho_abandonado_cupom5.mjml` $\to$ `mock_carrinho_abandonado_cupom5.html` (*STC 16*)
9. **Cupom 6 — Carrinho Abandonado 3**: `carrinho_abandonado_cupom6.mjml` $\to$ `mock_carrinho_abandonado_cupom6.html` (*STC 17*)

---

## 8. Integração Final no Backend

A geração dos e-mails foi completamente integrada aos **Workers Python** do sistema. O `BaseEmailBuilder` (`src/services/email_builders/base_builder.py`) foi reescrito para utilizar a engine do **Jinja2** e injetar não só os dados do pedido (`OrderTransitionEvent`), mas também todas as chaves do arquivo `brand_data.yml`.

Isso garante que:
- Assuntos dinâmicos configurados no YAML (`subject`) sejam embutidos diretamente pelas classes `ConcreteBuilders`.
- Os rodapés fiquem 100% corretos para qualquer alteração na loja (WhatsApp, E-mail de suporte).
- Não haja mais a necessidade de recompilar HTML a menos que uma alteração estrutural no layout do e-mail seja demandada.
  - **Botões Pill-Shape (`border-radius: 28px`)**: Formato arredondado moderno e acolhedor para as chamadas de ação (CTAs).
  - **Cards e Badges Promocionais**: Uso de contêineres arredondados com contraste alto entre `#1E3A8A` e fundos claros (`#F8FAFC`).
