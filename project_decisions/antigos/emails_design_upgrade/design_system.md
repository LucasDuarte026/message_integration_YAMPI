# Eleveme Email UI Design System

## 🎨 Design Foundations

### Color System
**Primary Colors**: 
- `Primary Base`: `#1E3A8A` (Deep Blue - transmite confiança, segurança e alinhamento com a identidade da marca 💙)
- `Primary Dark`: `#172554` (Para estados de hover em botões primários)

**Secondary Colors**: 
- `Secondary Base`: `#000000` (Usado para títulos de impacto e banners)
- `Secondary Light`: `#334155` (Slate 700 - Para textos descritivos)

**Neutral Palette**: 
- `Background`: `#F8FAFC` (Slate 50 - Fundo principal do e-mail, menos agressivo que branco puro)
- `Card/Container Background`: `#FFFFFF` (Branco puro para os blocos de conteúdo central)
- `Divider/Borders`: `#E2E8F0` (Slate 200 - Linhas de divisão sutis)

**Semantic Colors**: 
- `Success`: `#10B981` (Verde para "Pedido Aprovado" ✅)
- `Warning`: `#F59E0B` (Amarelo/Laranja para alertas de "Transportadora" ⚠️)
- `Promo/Discount`: `#EF4444` (Vermelho sutil para destacar preços riscados e descontos urgentes)

**Accessibility**: 
- Todas as combinações de texto principal (`#334155`) sobre fundo branco (`#FFFFFF`) e branco sobre o azul primário (`#1E3A8A`) excedem a taxa de contraste 4.5:1 exigida pelo WCAG AA.

### Typography System
**Primary Font**: `arial, 'helvetica neue', helvetica, sans-serif` (Inspirado no e-mail de referência Ferryhopper / Island Escape para máxima compatibilidade universal em todos os clientes de e-mail e renderização impecável no Outlook)
**Font Scale**: 
- Título Principal (H1): `24px`
- Título Secundário (H2): `20px`
- Texto Base (Body): `16px` (Garante leitura perfeita no celular sem zoom)
- Texto Auxiliar/Disclaimer: `12px` ou `14px`

**Font Weights**: 
- Regular: `400` (Corpo do texto)
- Bold: `700` (Títulos, Calls to Action e Destaques de Preço)

**Line Heights**: 
- Títulos: `120%`
- Texto Base: `150%` (Melhora escaneabilidade e respiro de leitura)

### Spacing System
**Base Unit**: `4px`
**Escala MJML**: 
- Margens internas dos contêineres: `24px` a `32px`
- Espaçamento entre blocos verticais: `16px` a `24px`
- Espaçamento de botões (Padding): `12px` vertical, `28px` horizontal

---

## 🧱 Component Library (MJML Patterns)

### Base Components

**Botão Primário (CTA - Estilo EML Referência)**:
- Background: `#1E3A8A` (ou Accent Teal `#2FBBA3` para promoções)
- Cor do Texto: `#FFFFFF`
- Border Radius: `28px` (Pill-shape arredondado característico do e-mail de referência)
- Fonte: `arial, 'helvetica neue', helvetica, sans-serif`, `15px Bold`
- Exemplo MJML: `<mj-button background-color="#1E3A8A" color="#FFFFFF" border-radius="28px" font-weight="bold" font-family="arial, 'helvetica neue', helvetica, sans-serif">Acompanhar Pedido</mj-button>`

**Regra de Imagens (Estrutura Padrão)**:
- Todo e-mail terá **exatamente duas imagens** principais:
  1. **Imagem fina no Topo (Header)**: Um banner retangular e fino no cabeçalho do e-mail (ex: `seu_carrinho_esta_te_esperando_header.png`).
  2. **Imagem quadrada no Corpo (Body)**: Uma imagem central de formato quadrático que ilustra a ação ou reforça o apelo no meio do conteúdo (ex: `pedido_aprovado.png` ou `5%desconto.png`).

**Cabeçalho (Header)**:
- Fundo transparente ou `#FFFFFF`.
- Segue a **Regra 1**: Inserção da Imagem Fina no topo.

**Bloco de Cross-sell / Produtos**:
- Estrutura de grid (duas colunas no desktop, empilhadas no mobile).
- Imagem do produto.
- Título: `16px Bold #334155`.
- Preço Riscado: `14px Regular #94A3B8` (com `text-decoration: line-through`).
- Preço Promocional: `18px Bold #10B981` ou `#EF4444`.
- Botão "Garantir oferta": Estilo secundário ou outline.

**Rodapé (Footer)**:
- Background: `#F1F5F9` ou `#1E293B` (Dark).
- Texto: `12px` centralizado.
- Ícones sociais (Instagram, Facebook, TikTok) alinhados ao centro com `width="24px"`.
- Disclaimer e contato de suporte destacados.

---

## 📱 Responsive Design (Mobile First)

### Breakpoint Strategy
Como os e-mails são lidos 70% das vezes no celular, a arquitetura MJML usará colunas empilháveis automáticas.
- **Mobile (<480px)**: 
  - Containers com `width="100%"`.
  - Botões esticados (full width) para facilitar clique com o polegar (Touch Target de no mínimo 44px).
- **Desktop (>480px)**: 
  - E-mail restrito a `max-width: 600px`.
  - Produtos de cross-sell exibidos lado a lado (`<mj-column width="50%">`).

---

## ♿ Accessibility Standards

### Inclusão e Acessibilidade (E-mail)
- **Alt Text**: Todas as imagens (`<mj-image>`), principalmente os banners promocionais da pasta `ref1/`, terão o atributo `alt` detalhado (ex: `alt="Banner: Seu carrinho ainda te espera com 10% de desconto"`).
- **Contraste**: Validação de cores de links, evitando azul claro sobre fundo branco.
- **Touch Targets**: Os links textuais e botões terão espaçamento suficiente para evitar cliques acidentais no mobile.

---
**UI Designer**: Antigravity (Agency UI Designer)
**Data do Design System**: 2026-07-27
**Status**: Pronto para Handoff (Desenvolvimento Frontend / MJML)
