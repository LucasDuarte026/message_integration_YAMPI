# Políticas de Entregabilidade, Domínios e Governança Antispam (SDD)

**Status:** Ativo / Norma Arquitetural de Entregabilidade  
**Versão Alvo:** `6.6.0`  
**Padrão:** SDD (*Spec-Driven Development*) · EARS (*Easy Approach to Requirements Syntax*) + Cenários `DADO / QUANDO / ENTÃO`  
**Documentos Relacionados:** [Especificações Formais SDD](./sdd_specs.md) · [Arquitetura do Sistema](./architecture.md) · [Máquina de Estados STG/STC](./email_state_machine.md) · [Diretrizes de Testes](./testing_guidelines.md)

---

## 1. Propósito e Arquitetura de Entregabilidade em 5 Camadas

Este documento especifica formalmente todas as regras de negócio, políticas técnicas e garantias operacionais adotadas pelo `message_integration` para assegurar entrega na caixa de entrada principal (*Inbox Placement*) junto aos grandes provedores (Google/Gmail, Yahoo Mail e Microsoft Outlook/Hotmail), eliminando os gatilhos que anteriormente levavam os disparos à caixa de Spam.

```mermaid
flowchart TD
    C1["Camada 1: Identidade DNS e Criptografia (SPF -all, DKIM 2048-bit + Oversigning, DMARC p=quarantine/reject)"] --> C2["Camada 2: Segregação de Fluxos e Domínios (Avisos Transacionais vs. Promoções/Recuperação)"]
    C2 --> C3["Camada 3: Higiene Anti-Graymail e Neutralidade Lexical (Sem Duplicatas, Sem Emojis/Urgência)"]
    C3 --> C4["Camada 4: Pipeline Visual WebP Otimizado (Inline CID Compressão Máxima ou Endpoint HTTPS)"]
    C4 --> C5["Camada 5: Pacote MIME Moderno (EmailMessage: RFC 2046 + RFC 5322 + RFC 8058)"]
```

### Por que cada medida é indispensável para as companhias de tráfego de e-mail?
Desde **fevereiro de 2024**, Google e Yahoo (acompanhados pelas exigências da Microsoft para remetentes comerciais) passaram a rejeitar ou rebaixar automaticamente mensagens que falham em quatro eixos matemáticos:
1. **Autenticação e Alinhamento (`SPF`, `DKIM`, `DMARC`):** comprovam criptograficamente que o servidor emissor pertence à marca exibida no `From:` e impedem falsificação (*spoofing*).
2. **Integridade Estrutural e de Cabeçalhos (`RFC 5322` e `RFC 2046`):** mensagens sem `Message-ID`, `Date` ou alternativa `text/plain` acumulam penalidade base de **+5,4 a +7,5 pontos** em motores como o SpamAssassin (onde **5,0** já classifica como Spam).
3. **Peso de Payload e Proporção Texto/Imagem:** anexos Base64 gigantes disparavam a regra `HTML_IMAGE_ONLY_08` e o corte de **102 KB do Gmail** (*Gmail Clipping*), ocultando CNPJ e links de descadastramento no rodapé.
4. **Engajamento e Baixo Índice de Reclamações (`RFC 8058` e Anti-Graymail):** o limite saudável de denúncias de spam no Google Postmaster Tools é **< 0,10%**, com zona crítica de bloqueio em **0,30%**. Fornecer `List-Unsubscribe: One-Click` e eliminar cópias não lidas (*Graymail*) protege diretamente essa métrica.

---

## 2. Política de Domínios e Segregação de Tráfego (Avisos vs. Promoções)

Os algoritmos de reputação avaliam o domínio remetente separando o comportamento de abertura e reclamação por identidade emissora. Misturar notificações essenciais de compra com ofertas comerciais de desconto expõe recibos e códigos de rastreio a penalidades causadas por clientes que marcam cupons como spam.

| Classificação do Fluxo | Estados da Máquina (`STG` / `STC`) | Natureza e Sinalizador (`is_promotional`) | Conta / Remetente Lógico & Evolução de Subdomínio | Cabeçalhos RFC 8058 (`List-Unsubscribe`) |
| :--- | :--- | :--- | :--- | :--- |
| **Avisos Transacionais Puros** | `STG 1` (`pedido_aprovado`), `STG 3` (`pedido_a_caminho`) | Estritamente operacional (`is_promotional = False`). Alta taxa de abertura esperada. | **`transactional@yourstore.com`** (pool `_server`). Evolução futura: `notify.yourstore.com`. | **Não injetado** (comunicação contratual essencial do pedido). |
| **Lembrete de Pagamento / Cobrança** | `STG 2` (`pedido_pendente`) | Transacional de checkout imediato (`is_promotional = False`). | **`transactional@yourstore.com`** (pool `_server`). | **Não injetado**. |
| **Promoções e Recuperação Comercial** | `STG 5, 6, 7` (`cupom_pedido_1..3`) e `STC 15, 16, 17` (`carrinho_abandonado_cupom4..6`) | Promocional / incentivo de conversão (`is_promotional = True`). | **`promotions@yourstore.com`** (pool `_promo_server` via `PROMO_SMTP_*`, com `Reply-To` e `rua=` isolados). Evolução futura: `promo.yourstore.com`. | **Obrigatório** (`List-Unsubscribe` + `List-Unsubscribe-Post: List-Unsubscribe=One-Click`). |

---

## 3. Consolidação das Alterações e Políticas por Fase (Fases 1 a 5)

### Fase 1 — Governança Operacional, Anti-Graymail e Neutralidade Semântica
* **Arquivos alterados:** [`src/core/macros.py`](../src/core/macros.py), [`src/core/config.py`](../src/core/config.py), [`src/templates/emails/config/brand_data.yml`](../src/templates/emails/config/brand_data.yml), `src/templates/emails/mjml/views/*.mjml`, `src/templates/emails/html_compiled/*.html`, `src/templates/emails/mocks/*.html` e [`tests/test_abandoned_cart.py`](../tests/test_abandoned_cart.py).
* **Modificações e garantias implementadas:**
  1. **Bloqueio de Graymail por duplicata:** `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH` alterado para `False` em [`macros.py`](../src/core/macros.py), evitando o envio paralelo de cópias que ficam sem abertura em caixa de supervisão e derrubam a taxa de engajamento do domínio.
  2. **Identidade centralizada:** definição de `MACRO_EMAIL_FROM_NAME`, `MACRO_EMAIL_REPLY_TO`, `MACRO_EMAIL_MESSAGE_ID_DOMAIN`, `MACRO_EMAIL_UNSUBSCRIBE_URL` e `MACRO_EMAIL_UNSUBSCRIBE_MAILTO`, expostos via `Config` / `load_config()` com suporte a sobrescrita por variáveis de ambiente.
  3. **Neutralidade lexical:** remoção integral de emojis de alerta/risco e de termos em CAIXA ALTA de urgência/desconto (`% OFF`, `ÚLTIMA CHANCE`, `🔥`, `⚠️`, `🎁`, `✨`, `🚨`, `📦`, etc.) nas linhas de assunto em `brand_data.yml`, nos arquivos fonte `.mjml`, nos HTMLs compilados e nos mocks regenerados via [`src/templates/emails/builder.py`](../src/templates/emails/builder.py).

---

### Fase 2 — Pipeline de Otimização Visual (WebP) e Política de Transporte de Imagens
* **Arquivos criados/alterados:** Pipeline offline de otimização WebP, `src/templates/emails/assets/images/**/*` (não versionados no GitHub), [`brand_data.yml`](../src/templates/emails/config/brand_data.yml) e [`tests/test_smtp_email_provider.py`](../tests/test_smtp_email_provider.py).
* **Modificações e resultados obtidos:**
  1. Preservação externa dos PNGs originais fora do repositório Git.
  2. Estudo comparativo automatizado avaliando múltiplos níveis de compressão WebP contra a referência original.
  3. Adoção do **Pipeline WebP Otimizado** com composição em fundo branco sólido `#FFFFFF` para transparências em todas as 22 imagens ativas, reduzindo o conjunto total de **14.237,3 KB para 524,3 KB (-96,3%)** e corrigindo extensões duplicadas anteriores (`.png.png`).
* **Política de Transporte de Imagens (Inline Otimizado vs. Endpoint HTTPS):**
  - **Modo padrão ativo (Inline Otimizado `cid:`):** graças à redução de **96,3%** no peso das imagens WebP, o envio inline (`Content-Disposition: inline`, MIME `image/webp`) mantém pontuação **`10 / 10` certificada** no Mail-Tester sem exigir servidor de mídia externo.
  - **Suporte nativo a Endpoint HTTPS/CDN:** caso caminhos em `brand_data.yml` apontem para URLs `https://...` (ex.: `https://cdn.yourstore.com/assets/emails/...`), o [`SMTPEmailProvider`](../src/ports/smtp_email_provider.py) detecta automaticamente e **não anexa nenhum binário**, reduzindo o pacote abaixo de **25 KB**.

---

### Fase 3 — Geração Automática de Alternativa em Texto Puro (`text/plain` — RFC 2046)
* **Arquivos criados/alterados:** [`src/services/email_builders/base_builder.py`](../src/services/email_builders/base_builder.py) e [`tests/test_email_plain_text.py`](../tests/test_email_plain_text.py).
* **Modificações e garantias:**
  1. Implementação do parser `_HTMLToPlainTextParser` (biblioteca padrão `html.parser`) e dos métodos `html_to_plain_text()` e `build_with_plain_text()` em `BaseEmailBuilder`.
  2. Remoção automática de blocos `<style>`, `<script>`, `<head>`, `<title>` e comentários condicionais do Outlook (`<!--[if mso]>`), preservando saudação, itens, valores, código PIX, código de rastreio, links `https://` em texto legível e dados legais no rodapé.

---

### Fase 4 — Modernização do Pacote MIME e Conformidade RFC 5322 / RFC 8058
* **Arquivos alterados:** [`src/domain/interfaces.py`](../src/domain/interfaces.py), [`src/ports/message_provider.py`](../src/ports/message_provider.py), [`src/ports/smtp_email_provider.py`](../src/ports/smtp_email_provider.py), [`src/services/notification_service.py`](../src/services/notification_service.py), [`src/main.py`](../src/main.py), [`src/debug_main.py`](../src/debug_main.py) e [`tests/test_smtp_email_provider.py`](../tests/test_smtp_email_provider.py).
* **Modificações e garantias:**
  1. Migração de `MIMEMultipart`/`MIMEText`/`MIMEImage` legados para `email.message.EmailMessage` (Python 3.12).
  2. Injeção sistemática de cabeçalhos RFC 5322: `Message-ID` único por envio (`make_msgid(domain=...)`), `Date` local formatado (`formatdate(localtime=True)`), `From` humanizado com nome da marca (`formataddr`) e `Reply-To` para atendimento.
  3. Montagem estrita `multipart/alternative` com `text/plain` precedendo `text/html` (RFC 2046) e suporte a `add_related` com MIME `image/webp` exclusivamente para caminhos locais.
  4. Injeção condicional de `List-Unsubscribe` e `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058) quando `is_promotional=True` (cupons de pedido e carrinhos abandonados).

---

### Fase 5 — Certificação DNS, Alinhamento Criptográfico e Telemetria (`10/10` Validado)
* **Escopo:** Zona DNS autoritativa do domínio emissor, relay SMTP autenticado e monitoramento contínuo de reputação.
* **Políticas estabelecidas e certificadas (ambos os fluxos: Transacional e Promocional):**
  1. **SPF Estrito (`-all`):** registro único `TXT` na raiz de `yourstore.com` terminando com `-all` (*HardFail*), mantendo `<= 10` *lookups* DNS, alinhamento nativo de `Return-Path` (`MAIL FROM`) e preservação de eventuais subdomínios de plataformas terceiras sob alinhamento relaxado.
  2. **DKIM Criptográfico (2048 bits + Oversigning RFC 6376):** assinatura ativa com chave RSA de 2048 bits no seletor ativo de saída (além de seletores de rotação gerida) e *oversigning* dos cabeçalhos críticos (`From`, `Reply-To`, `Subject`, `Date`, `Message-ID`, `List-Unsubscribe`).
  3. **DMARC Coercivo e Privacidade (LGPD):** registro `TXT` em `_dmarc.yourstore.com` configurado com `v=DMARC1; p=quarantine; pct=100; rua=mailto:promotions@yourstore.com; adkim=r; aspf=r;` (com evolução para `p=reject` após janela de validação de relatórios XML e **proibição de `ruf=`** sem criptografia para evitar vazamento de PII).
  4. **Certificação Empírica (`10/10` Mail-Tester + Google Postmaster Tools):** nota máxima `10/10` validada para fluxos **informativos/transacionais** e **promocionais**, `0` blocklists IPv4, rDNS/FCrDNS válido, TLS ativo e domínio verificado no Google Postmaster Tools mantendo *User-Reported Spam* `< 0,10%` (teto crítico `0,30%`).
  5. **Segregação de Subdomínios e Escala:** preparação para subdomínios dedicados (`notify.yourstore.com` vs. `promo.yourstore.com`) ou ESP REST dedicado caso o volume cresça para patamares de *Bulk Sender* (`>= 5.000 e-mails/dia`).

---

## 4. Requisitos Normativos SDD (EARS + Cenários Verificáveis)

### `POL-EMAIL-01` — Identidade RFC 5322 e Ordem da Árvore MIME (RFC 2046)
* **Requisito (EARS):**
  1. Todo e-mail despachado pelo `SMTPEmailProvider` **DEVE** conter cabeçalhos `Message-ID` único no domínio configurado (`EMAIL_MESSAGE_ID_DOMAIN`), `Date` válido em formato RFC 2822, `From` formatado com nome amigável (`EMAIL_FROM_NAME`) e `Reply-To` (`EMAIL_REPLY_TO`).
  2. Todo e-mail **DEVE** possuir estrutura `multipart/alternative` onde a parte `text/plain` precede estruturalmente a parte `text/html`.
* **Cenário Verificável:**
  * **DADO** uma chamada a `SMTPEmailProvider.send_email_message` com `html_body` e `plain_text`
  * **QUANDO** a mensagem MIME é serializada para envio SMTP
  * **ENTÃO** os cabeçalhos `Message-ID`, `Date`, `From` e `Reply-To` estão presentes e `text/plain` aparece antes de `text/html` no caminhamento da árvore MIME.

### `POL-EMAIL-02` — Roteamento Dual de Remetentes e Descadastramento One-Click (RFC 8058)
* **Requisito (EARS):**
  1. Quando o disparo for proveniente de cupons de pedido (`cupom_pedido_1..3`) ou carrinhos abandonados (`carrinho_abandonado_cupom4..6`), o `NotificationService` **DEVE** definir `is_promotional=True` e o provedor **DEVE** autenticar e despachar pela conta promocional (`PROMO_SMTP_USER`/`PROMO_SMTP_FROM` = `promotions@yourstore.com`, com fallback seguro para a conta principal se não configurada) injetando `List-Unsubscribe` (`HTTPS` + `mailto:promotions@yourstore.com`) e `List-Unsubscribe-Post: List-Unsubscribe=One-Click`.
  2. Quando o disparo for transacional operacional (`pedido_aprovado`, `pedido_pendente`, `pedido_a_caminho`), o `NotificationService` **DEVE** definir `is_promotional=False`, o provedor **DEVE** autenticar e despachar pela conta principal (`transactional@yourstore.com`) e **NÃO DEVE** injetar cabeçalhos `List-Unsubscribe`.
  3. Em ambos os fluxos, `Reply-To` **DEVE** rotear para o endereço de atendimento configurado (`EMAIL_REPLY_TO`), mantendo isolamento de conexões e tolerância a falhas entre os dois pools SMTP.
* **Cenário Verificável:**
  * **DADO** um evento `CartTransitionEvent` roteado para `carrinho_abandonado_cupom4`
  * **QUANDO** `handle_cart_transition` aciona o provedor
  * **ENTÃO** `List-Unsubscribe-Post: List-Unsubscribe=One-Click` está presente no cabeçalho do pacote final.

### `POL-EMAIL-03` — Política de Ativos Visuais (WebP Otimizado Inline / Suporte HTTPS)
* **Requisito (EARS):**
  1. Quando um atributo `src` ou `background` no HTML iniciar com `https://` ou `http://` (cenário de endpoint externo/CDN), o `SMTPEmailProvider` **NÃO DEVE** baixar, converter em `cid:` ou anexar binários de imagem na mensagem SMTP.
  2. Enquanto os ativos permanecerem em armazenamento local, todas as imagens **DEVEM** utilizar o **Pipeline WebP Otimizado** (composição em fundo sólido `#FFFFFF` em transparências), sendo anexadas como `image/webp` inline via `add_related` sobre a parte HTML.
* **Cenário Verificável:**
  * **DADO** um HTML contendo `<img src="https://cdn.yourstore.com/assets/emails/banner.webp" />`
  * **QUANDO** `send_email_message` constrói o objeto `EmailMessage`
  * **ENTÃO** nenhuma parte `image/*` é anexada ao pacote MIME.

### `POL-EMAIL-04` — Neutralidade Semântica e Prevenção de Graymail
* **Requisito (EARS):**
  1. Em modo padrão de produção, `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH` **DEVE** permanecer `False` para impedir acúmulo de cópias não abertas na caixa de supervisão.
  2. Assuntos (`brand_data.yml`) e corpos dos templates (`.mjml` / `html_compiled/*.html`) **NÃO DEVEM** conter emojis de risco/urgência ou expressões agressivas em caixa alta associadas a filtros antispam.

### `POL-EMAIL-05` — Conformidade Criptográfica DNS e Governança de Reputação
* **Requisito (EARS):**
  1. A zona DNS autoritativa do domínio emissor **DEVE** manter `SPF` com terminação `-all` (`<= 10` lookups), `DKIM` RSA de 2048 bits publicado no seletor ativo de saída (pré-requisito obrigatório antes do endurecimento coercivo) e `DMARC` coercivo (`p=quarantine` ou `p=reject`, `pct=100`, `adkim=r`, `aspf=r`, `rua=` ativo e ausência de `ruf=`).
  2. O monitoramento no Google Postmaster Tools **DEVE** garantir taxa de reclamações inferior a `0,10%` (gatilho de suspensão imediata de fluxos promocionais ao atingir `0,30%`).

### `POL-EMAIL-06` — Governança de Escala para *Bulk Senders* (`>= 5.000 e-mails/dia` — RFC 8058 & Supressão)
* **Requisito (EARS):**
  1. Caso o volume diário de envios ao Gmail se aproxime ou ultrapasse **5.000 mensagens em 24 horas** (*Bulk Sender* permanente segundo diretrizes Google/Yahoo), o sistema **DEVE** operar um endpoint `HTTPS` real de *One-Click Unsubscribe* capaz de responder `HTTP 200 OK` para requisições `POST` (`List-Unsubscribe=One-Click`) **sem redirecionamentos (`301`/`302`)**, **sem autenticação/cookies** e utilizando **token opaco único por destinatário**.
  2. Ao atingir esse patamar de escala, toda solicitação de descadastramento **DEVE** suprimir automaticamente novos envios promocionais ao destinatário em até **48 horas** (via ESP dedicado com supressão nativa ou tabela de supressão no PostgreSQL acoplada ao servidor HTTP), além de incluir **link visível de descadastramento no corpo HTML** das mensagens promocionais.
* **Cenário Verificável:**
  * **DADO** um disparo promocional classificado em regime de *Bulk Sender* (`>= 5.000 e-mails/dia`) com token opaco no `List-Unsubscribe`
  * **QUANDO** o provedor de caixa postal executa `POST` com corpo `List-Unsubscribe=One-Click`
  * **ENTÃO** o endpoint responde `HTTP 200 OK` diretamente sem redirect e registra o bloqueio promocional do destinatário em até 48 horas.
