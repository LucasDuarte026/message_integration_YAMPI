<div align="center">

<a href="./images/resume/showcase_carousel.webp">
  <img src="./images/resume/showcase_carousel.webp" alt="Message Integration — Production Showcase Carousel (Overview, Architecture, State Machine & RFC, Live Proof, Hardening & Benchmarks)" width="100%" />
</a>

<sub>
  <strong>Auto-playing Showcase (v0)</strong> — Open any full-resolution plate:
  <a href="./images/resume/hero_featured_1200x627.png">01 · Overview</a> &nbsp;|&nbsp;
  <a href="./images/resume/plate_1_architecture_1600x1000.png">02 · Architecture</a> &nbsp;|&nbsp;
  <a href="./images/resume/plate_2_state_and_rfc_1600x1000.png">03 · State Machine &amp; RFC</a> &nbsp;|&nbsp;
  <a href="./images/resume/plate_3_live_proof_1600x1000.png">04 · Live Proof</a> &nbsp;|&nbsp;
  <a href="./images/resume/plate_4_hardening_and_impact_1600x1000.png">05 · Hardening &amp; Benchmarks</a>
</sub>

<br />

<details>
  <summary>🖼️ <strong>Expand Full-Width Static Gallery (All 5 Plates at 100% Width)</strong></summary>
  <br />
  <p><strong>01 · Production Overview</strong></p>
  <img src="./images/resume/hero_featured_1200x627.png" alt="Slide 01 — Production Overview" width="100%" />
  <br /><br />
  <p><strong>02 · Clean / Hexagonal Architecture</strong></p>
  <img src="./images/resume/plate_1_architecture_1600x1000.png" alt="Slide 02 — Clean / Hexagonal Architecture" width="100%" />
  <br /><br />
  <p><strong>03 · Dual-Track ACID State Machine &amp; RFC Pipeline</strong></p>
  <img src="./images/resume/plate_2_state_and_rfc_1600x1000.png" alt="Slide 03 — State Machine & RFC Pipeline" width="100%" />
  <br /><br />
  <p><strong>04 · Live Production Proof (10/10 Deliverability &amp; Sentry APM)</strong></p>
  <img src="./images/resume/plate_3_live_proof_1600x1000.png" alt="Slide 04 — Live Production Proof" width="100%" />
  <br /><br />
  <p><strong>05 · Hardening, Quality Gates &amp; Industry Benchmarks</strong></p>
  <img src="./images/resume/plate_4_hardening_and_impact_1600x1000.png" alt="Slide 05 — Hardening & Benchmarks" width="100%" />
</details>

</div>

---

# 🚀 Message Integration Yampi

[![Release Status](https://img.shields.io/badge/Release-STABLE-success?style=for-the-badge&logo=rocket)](https://github.com/LucasDuarte026/message_integration_YAMPI/releases)
[![Tests](https://img.shields.io/badge/Tests-140%20Tests%20(85%25%2B%20Cov)-brightgreen?style=for-the-badge&logo=pytest)](./docs/testing_guidelines.md)
[![Email Deliverability](https://img.shields.io/badge/Deliverability-10%2F10%20Certified%20%7C%20RFC%20Compliant-brightgreen?style=for-the-badge&logo=gmail)](./docs/email_deliverability_policies.md)
[![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue?style=for-the-badge&logo=python)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-Clean%20%2F%20Hexagonal-orange?style=for-the-badge)](./docs/architecture.md)
[![Database](https://img.shields.io/badge/Database-PostgreSQL%20Pool-336791?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Observability](https://img.shields.io/badge/Observability-Sentry%20APM-362D59?style=for-the-badge&logo=sentry)](https://sentry.io/)
[![Docker](https://img.shields.io/badge/Docker-Production%20Ready-2496ED?style=for-the-badge&logo=docker)](https://www.docker.com/)

> **Enterprise-grade, event-driven message orchestration and sales recovery engine built specifically for high-conversion e-commerce stores on the Yampi platform.**

## 📑 Table of Contents

- [💡 Why This Exists](#-why-this-exists)
- [📊 Business Impact & Industry Benchmarks](#-business-impact--industry-benchmarks)
- [🏛️ High-Level Architecture](#️-high-level-architecture)
- [✨ Key Platform Pillars & Capabilities](#-key-platform-pillars--capabilities)
- [📧 Email Deliverability Certification (10/10) & Anti-Spam Compliance](#-email-deliverability-certification-1010--anti-spam-compliance)
- [📡 Production Observability, Cloud APM & Sentry Telemetry](#-production-observability-cloud-apm--sentry-telemetry)
- [🔒 Security & Pre-Release Governance](#-security--pre-release-governance)
- [⚡ Quick Start & Deployment](#-quick-start--deployment)
- [📚 Technical Documentation & AI Agents](#-technical-documentation--ai-agents)
- [📄 License and Commercial Use](#-license-and-commercial-use)

---

## 💡 Why This Exists

According to the **[Baymard Institute](https://baymard.com/lists/cart-abandonment-rate)** (meta-analysis of 50 global e-commerce studies, 2006–2025), online stores lose an average of **70.22% of shopping carts to abandonment**—rising to **79.53%–80.45% on mobile** vs. **68.62%–69.56% on desktop** ([Dynamic Yield](https://www.indez.com/cart-abandonment-statistics)) and **79%–82% in Brazil** ([Opinion Box 2026](https://blog.opinionbox.com/abandono-de-carrinho/) / [E-commerce Radar](https://comprarapida.co/blog/taxa-de-abandono-de-carrinho-brasil-2026-benchmark-por-segmento)), where **82%** of consumers report returning via email coupons and **27%** abandon due to broken or invalid coupon codes. In the Brazilian market specifically, **PIX accounts for 49% of online purchases** ([Nuvemshop](https://www.nuvemshop.com.br/blog/pix-ecommerce/)) and **55.2% of all national payment transactions** ([Banco Central](https://www.bcb.gov.br/)), yet roughly **1 in 4 PIX checkouts expire unpaid** (~75% average conversion, [PagBrasil](https://www.pagbrasil.com/pt-br/metodos-de-pagamento/pix/)), alongside **40%–60%** unpaid *boleto* estimates—a full-margin revenue leak that international marketing suites rarely address. Meanwhile, conventional email tools frequently trigger duplicate sends on overlapping polling cycles or API retries, degrade in corporate/Outlook clients that block remote images (while Apple Mail Privacy Protection obscures open-rate tracking), and fail under sudden concurrency spikes.

**Message Integration** addresses these failure modes through deterministic backend engineering:
- 🛒 **Configurable Automated Sales Recovery**: Re-engages abandoned carts through multi-stage sequences configurable via [`src/core/macros.py`](./src/core/macros.py) (default `4h, 24h, 48h, 96h`) with immediate state-driven conversion freeze (`order_id IS NOT NULL`) upon purchase.
- ⚡ **Full-Margin Payment Acceleration**: Triggers timely `STG 2` reminders (`5–30 min`) for pending PIX and bank slip (*boleto*) orders before expiration, recovering high-intent sales at **0% discount (full margin)**.
- 📦 **Automated Order Tracking & Corporate Legibility**: Dispatches carrier tracking codes proactively as soon as orders reach `STG 3` fulfillment—cutting post-purchase *WISMO* support load—while RFC 2046 `multipart/alternative` (`text/plain` + HTML/CSS) guarantees readability across Outlook/corporate clients and anchors optimization on clicks and completed orders.
- 🛡️ **Strict Business-Event Idempotency & Fault-Tolerant Delivery**: PostgreSQL ACID state machine (`SELECT ... FOR UPDATE` row locks + `COALESCE(LEAST(...))` temporal guard) with exponential backoff and `at-least-once` SMTP delivery safety (honoring [RFC 5321 Section 6.1](https://datatracker.ietf.org/doc/html/rfc5321#section-6.1)) to prevent duplicate business triggers across concurrent workers or repeated polling cycles.

---

## 📊 Business Impact & Industry Benchmarks

> Industry baselines below are anchored in audited 2025–2026 primary research—**[Baymard Institute](https://baymard.com/lists/cart-abandonment-rate)**, **[Dynamic Yield](https://www.indez.com/cart-abandonment-statistics)**, **[Opinion Box 2026](https://blog.opinionbox.com/abandono-de-carrinho/)**, **[Klaviyo 2026](https://www.klaviyo.com/blog/abandoned-cart-benchmarks)**, **[Nuvemshop](https://www.nuvemshop.com.br/blog/pix-ecommerce/)**, **[Banco Central](https://www.bcb.gov.br/)**, **[PagBrasil](https://www.pagbrasil.com/pt-br/metodos-de-pagamento/pix/)**, **[Validity 2026](https://www.validity.com/resource-center/2026-email-deliverability-benchmark-report/)**, **[Gorgias](https://www.gorgias.com/blog/automate-wismo-requests)**, and **[Deloitte Digital 2026](https://www.deloitte.com/global/en/services/consulting/perspectives/global-contact-center-survey.html)**—paired with this repository's verified runtime telemetry and RFC protocol certification.

| Dimension | Industry Baseline (2025–2026 Audited Sources) | With Message Integration (Audited) | Direct Engineering & Business Outcome |
| :--- | :--- | :--- | :--- |
| **Cart Abandonment** | **70.22%** Global ([Baymard](https://baymard.com/lists/cart-abandonment-rate), 50 studies) · **79.53%–80.45%** Mobile ([Dynamic Yield](https://www.indez.com/cart-abandonment-statistics)) · **79%–82%** Brazil ([Opinion Box](https://blog.opinionbox.com/abandono-de-carrinho/) / [E-commerce Radar](https://comprarapida.co/blog/taxa-de-abandono-de-carrinho-brasil-2026-benchmark-por-segmento)) | **Configurable Multi-Stage Recovery (`STC 15–18`)** via `macros.py` with instant conversion freeze (`order_id IS NOT NULL`) | 📈 Targets the highest-ROI automated flow (**3.33%** avg. placed-order rate, **$6.77–$13.70 RPR**, and **~41%** of attributed email revenue from **5.3%** of volume, [Klaviyo 2026](https://www.klaviyo.com/blog/abandoned-cart-benchmarks)); **82%** of Brazilian shoppers return via coupon emails |
| **Pending PIX & Boleto** | PIX = **49%** of BR e-commerce ([Nuvemshop](https://www.nuvemshop.com.br/blog/pix-ecommerce/)) & **55.2%** of national transactions ([Banco Central](https://www.bcb.gov.br/)); **~75%** avg. PIX conversion ([PagBrasil](https://www.pagbrasil.com/pt-br/metodos-de-pagamento/pix/)); **40%–60%** unpaid *boleto* estimates | **Pre-Expiration `STG 2` (`5–30 min`) PIX/Boleto Nudges** + deterministic status freeze upon payment capture | ⚡ Recovers expiring high-intent checkouts at **full margin (0% discount)** without colliding with already-paid orders |
| **Deliverability & Sender Mandates** | **87.2%** Global Inbox · **89.0%** Brazil · **77.4%** Microsoft Outlook ([Validity 2026](https://www.validity.com/resource-center/2026-email-deliverability-benchmark-report/)); mandatory Google/Yahoo (2024) & Microsoft (May 2025 `550 5.7.515`) enforcement | **`10/10` Mail-Tester Static Protocol Certification (`-0.2` SpamAssassin)** + Dual-SMTP stream isolation + Google Postmaster Tools | 🎨 `SPF -all`, `2048-bit DKIM`, `DMARC p=quarantine`, RFC 5322/2046 (`multipart/alternative`) & RFC 8058—preventing `550 5.7.515` rejections while isolating transactional vs. promotional domain reputation |
| **Post-Purchase Support (*WISMO*)** | **18%–33%** pure WISMO tickets, up to **~51%** incl. delivery issues ([Gorgias](https://www.gorgias.com/blog/automate-wismo-requests)); **$7.80** global ([Deloitte 2026](https://www.deloitte.com/global/en/services/consulting/perspectives/global-contact-center-survey.html)) to **$12.40** US manual cost ([Gorgias](https://www.gorgias.com/blog/automate-wismo-requests)) | **Automated `STG 3` Carrier Tracking Dispatch** upon fulfillment | 📦 Proactively delivers tracking codes—deflecting repetitive *"Where is my order?"* tickets where shoppers check status **4.6x** per order |
| **Runtime Stability & Orchestration** | Generic marketing tools suffer from polling race conditions, duplicate triggers & silent SMTP drops | **PostgreSQL ACID `FOR UPDATE` State Machine** + `at-least-once` backoff; **`1,030+`** accepted SMTP dispatches, **`0`** unresolved Sentry issues & **95-min** load test | 🛡️ Strict business-event idempotency (honoring [RFC 5321 §6.1](https://datatracker.ietf.org/doc/html/rfc5321#section-6.1)), fail-safe rollback on SMTP failure, and **0** acute memory leaks observed under sustained load |

<details>
  <summary>📚 <strong>Audited Industry & RFC References (2025–2026)</strong></summary>

- **Cart Abandonment (Global & Mobile):** [Baymard Institute — Cart Abandonment Rate Statistics (70.22%, 50 studies)](https://baymard.com/lists/cart-abandonment-rate) · [Dynamic Yield / Indez — Mobile vs. Desktop Abandonment (79.53%–80.45%)](https://www.indez.com/cart-abandonment-statistics)
- **Cart Abandonment (Brazil):** [Opinion Box 2026 — Abandono de Carrinho no Brasil (79%, 82% coupon return, 27% broken coupons)](https://blog.opinionbox.com/abandono-de-carrinho/) · [E-commerce Radar / Compra Rápida — Brazil Segment Benchmark (~82%)](https://comprarapida.co/blog/taxa-de-abandono-de-carrinho-brasil-2026-benchmark-por-segmento)
- **Email Recovery Economics:** [Klaviyo 2026 — Abandoned Cart Benchmarks (3.33% avg. placed order rate, $6.77–$13.70 RPR)](https://www.klaviyo.com/blog/abandoned-cart-benchmarks)
- **Brazil PIX & Boleto:** [Nuvemshop — PIX no E-commerce (49% share)](https://www.nuvemshop.com.br/blog/pix-ecommerce/) · [Banco Central do Brasil — Estatísticas de Pagamentos (55.2% PIX share)](https://www.bcb.gov.br/) · [PagBrasil — PIX Payment Conversion (~75% avg.)](https://www.pagbrasil.com/pt-br/metodos-de-pagamento/pix/)
- **Deliverability & Bulk Sender Mandates:** [Validity 2026 Email Deliverability Benchmark Report (87.2% global, 89.0% Brazil, 77.4% Microsoft)](https://www.validity.com/resource-center/2026-email-deliverability-benchmark-report/) · [Google Email Sender Guidelines](https://support.google.com/a/answer/81126) · [Microsoft High-Volume Sender Requirements (May 2025 `550 5.7.515`)](https://techcommunity.microsoft.com/blog/microsoftdefenderforoffice365blog/strengthening-email-ecosystem-outlook%E2%80%99s-new-requirements-for-high%E2%80%90volume-senders/4399730)
- **Post-Purchase WISMO Support:** [Gorgias — Automating WISMO Requests (18%–33% pure / ~51% combined, $12.40 US manual cost)](https://www.gorgias.com/blog/automate-wismo-requests) · [Deloitte Digital 2026 — Global Contact Center Survey ($7.80 global cost/contact)](https://www.deloitte.com/global/en/services/consulting/perspectives/global-contact-center-survey.html)
- **IETF Protocol Standards:** [RFC 5321 §6.1 (SMTP Reliable Delivery & Duplicate Semantics)](https://datatracker.ietf.org/doc/html/rfc5321#section-6.1) · [RFC 5322 (Internet Message Format)](https://datatracker.ietf.org/doc/html/rfc5322) · [RFC 2046 (MIME `multipart/alternative`)](https://datatracker.ietf.org/doc/html/rfc2046) · [RFC 8058 (One-Click Unsubscribe)](https://datatracker.ietf.org/doc/html/rfc8058)

</details>

---

## 🏛️ High-Level Architecture

```mermaid
flowchart TD
    YampiAPI["🛒 Yampi E-commerce API"] -->|Real-time Events / Polling| Daemon["⚙️ Autonomous Daemon Orchestrator"]
    
    Daemon --> WorkerCart["🛒 Abandoned Cart Worker"]
    Daemon --> WorkerOrder["📦 Orders & Tracking Worker"]
    
    subgraph StateMachine["🛡️ Dual-Track State Machine (PostgreSQL Pool)"]
        WorkerCart -->|ACID Lock| STC[("STC: 4h ➔ 24h ➔ 48h ➔ 96h")]
        WorkerOrder -->|ACID Lock| STG[("STG: Pending ➔ Approved ➔ Dispatched")]
    end
    
    subgraph DeliveryEngine["🎨 High-Deliverability Multi-Channel Engine"]
        WorkerCart --> MJML["Responsive MJML / Jinja2 + text/plain"]
        WorkerOrder --> MJML
        MJML --> CID["Optimized WebP Asset Pipeline / Inline CID"]
        CID --> SMTP["📧 Dual SMTP Routing: transactional@ & promotions@"]
        CID --> WhatsApp["💬 Meta WhatsApp Cloud API"]
    end
    
    subgraph Observability["📡 Observability & Cloud APM"]
        Daemon -.-> SentryCrons["Sentry Heartbeat Crons"]
        DeliveryEngine -.-> SentryTracing["Sentry Metrics, Spans & LGPD Tracebacks"]
    end
```

---

## ✨ Key Platform Pillars & Capabilities

### 1. 🛒 Precision Cart Recovery (STC State Machine)
- **STC 15 (4 Hours)**: Instant 10% discount trigger with a direct recovery checkout link (`simulate_url`).
- **STC 16 (24 Hours)**: Follow-up email highlighting scarcity, product benefits, and an upgraded 15% discount.
- **STC 17 (48 Hours)**: Final last-chance 20% discount coupon before automatic terminal transition (`STC 18` at 96 Hours).
- **Anti-Spam Conversion Guard**: Detects when a cart converts into an active order (`order_id IS NOT NULL`) and instantly freezes `stc`.

### 2. 📦 Transactional Lifecycle Engine (STG State Machine)
- **PIX / Boleto Pending (STG 2)**: Prompt reminder between 5 and 30 minutes boosting instant transfer conversion.
- **Order Approved (STG 1)**: Instant transactional receipt confirming payment capture (evolves `1 → 3` when dispatched).
- **On Carriage / In Transit (STG 3)**: Automatic tracking code delivery (`tracking_code` required) upon carrier dispatch.
- **Coupon Recovery (STG 4 → 5 → 6 → 7 → 8)**: Timed discount chain (`24h` 10%, `48h` 15%, `72h` 20%, `96h` lost) for unpaid orders.

### 3. 🛡️ Industrial-Grade Fault Tolerance
- **PostgreSQL Connection Pool**: `ThreadedConnectionPool` (`1–20` connections) prevents socket leaks and Docker DNS deadlocks.
- **Resilient HTTP Engine**: Automatic retries with exponential backoff (2s, 4s, 8s) for transient Yampi 5xx/Timeout errors.
- **SMTP Throttling & Mutex Locks**: Smooths multi-threaded dispatches into a regulated funnel, preventing rate-limit blacklisting.
- **Fail-Safe State Rollback**: Prevents database state transitions if email dispatch fails, guaranteeing organic retries in subsequent cycles.

### 4. 🎨 Visual Excellence, RFC Compliance & Dual SMTP Routing
- **MJML + Jinja2 + `text/plain` (RFC 2046/5322/8058)**: Mobile-first layouts with automatic `text/plain` alternative, `Message-ID`, `Date`, `Reply-To`, and `List-Unsubscribe: One-Click` headers on promotional flows.
- **Modular WebP Assets (`EMAIL_ASSETS_DIR`)**: Inline Content-ID (CID) image embedding or external HTTPS CDN links via an optimized WebP asset pipeline with 96.3% payload compression.
- **Dual SMTP Sender Isolation**: Separates transactional notifications (`transactional@`) from promotional coupon flows (`promotions@` via `PROMO_SMTP_*`) with transparent fallback.

---

## 📧 Email Deliverability Certification (10/10) & Anti-Spam Compliance

The **Yampi + Email Messaging Engine** and its authoritative **DNS zone** were audited and hardened end-to-end against modern inbox-provider enforcement mandates (Google, Yahoo, and Microsoft), achieving a **`10/10` anti-spam certification** across **both** outbound email categories:
1. **Informational & Transactional Flows** (payment confirmations, PIX/payment reminders, and shipping tracking notifications).
2. **Promotional & Sales Recovery Flows** (abandoned cart sequences and progressive recovery discount coupons).

### 1. Mail-Tester 10/10 Audit (Informational & Promotional Flows) & Google Postmaster Tools

Both independent sender streams (`transactional@` and `promotions@`) scored **`10/10`** in Mail-Tester with zero blocklist hits, zero broken links, and full cryptographic authentication, alongside continuous sender telemetry in **Google Postmaster Tools**:

| Mail-Tester `10/10` Certification (Transactional & Promotional) | Google Postmaster Tools Compliance Telemetry |
| :---: | :---: |
| ![Mail-Tester 10/10 Deliverability Certification](./images/mail_tester_com.png) | ![Google Postmaster Tools Compliance Status](./images/postMaster_errado.png) |

> [!NOTE]
> The Google Postmaster Tools screenshot above reflects the baseline capture prior to Google's daily telemetry refresh after DNS DKIM activation; live `SPF`, `DKIM (2048-bit)`, and `DMARC` validation are already certified at **`10/10`** in Mail-Tester across both sending channels.

### 2. Complete Deliverability & Anti-Spam Compliance Matrix

| Compliance Pillar / Standard | Technical Implementation in Engine & DNS Zone | Certification Result |
| :--- | :--- | :--- |
| **SPF (`RFC 7208`)** | Authoritative DNS `TXT` record enforcing strict `-all` (*HardFail*), `< 10` DNS lookups, and native `Return-Path` (`MAIL FROM`) envelope alignment. | **PASS / Compliant** |
| **DKIM (`RFC 6376`)** | 2048-bit RSA asymmetric cryptographic signing on active outbound selector with header oversigning (`From`, `Reply-To`, `Subject`, `Date`, `Message-ID`, `List-Unsubscribe`) and key rotation selectors. | **PASS / 10/10 Certified** |
| **DMARC (`RFC 7489`)** | Coercive domain policy (`p=quarantine` progressing to `p=reject`, `pct=100`), relaxed organizational alignment (`adkim=r; aspf=r;`), daily aggregate XML telemetry (`rua=`), and strict LGPD zero-PII protection (`ruf=` omitted). | **PASS / Compliant** |
| **One-Click Unsubscribe (`RFC 8058` & `RFC 2369`)** | Conditional injection of `List-Unsubscribe` (`HTTPS` + `mailto:`) and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` exclusively on promotional/recovery flows (`is_promotional=True`), paired with `>= 5,000 emails/day` Bulk Sender suppression governance. | **PASS / Compliant** |
| **Honor Unsubscribe & Spam Rate Gate** | Automated opt-out compliance window (`<= 48h`) and continuous Google Postmaster Tools monitoring enforcing user-reported spam strictly below `0.10%` (`0.30%` hard cutoff). | **Compliant (< 0.10% Spam)** |
| **MIME Tree & Headers (`RFC 5322` & `RFC 2046`)** | Modern `EmailMessage` architecture serializing `text/plain` fallback prior to `text/html`, unique domain-aligned `Message-ID`, RFC 2822 local `Date`, friendly `From`, and dedicated support `Reply-To`. | **PASS (`0.0` Penalty)** |
| **Transport Security (`TLS`), `rDNS` & IP Reputation** | Encrypted TLS SMTP transport, forward-confirmed reverse DNS (`FCrDNS` / `PTR` matching `HELO` and `A` record), valid `MX` routing, and clean reputation across 20+ IPv4 blocklists (Spamhaus, Barracuda, SpamCop, Mailspike, DNSWL). | **PASS / 0 Blocklists** |
| **SpamAssassin, Anti-Graymail & Payload Hygiene** | Neutralized transactional copywriting, duplicate supervision dispatch disabled (`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = False`), optimized WebP asset pipeline preventing 102 KB Gmail clipping, 100% image `alt` coverage, and zero broken links or URL shorteners. | **PASS (`-0.2` Score / `10/10`)** |
| **Dual SMTP Sender Isolation** | Dedicated connection pools separating transactional lifecycle receipts (`transactional@`) from promotional cart/order recovery campaigns (`promotions@`) under thread-safe mutex locks and exponential backoff. | **PASS / Isolated Pools** |

👉 **Full Spec-Driven Deliverability Policies:** [`docs/email_deliverability_policies.md`](./docs/email_deliverability_policies.md)

---

## 📡 Production Observability, Cloud APM & Sentry Telemetry

Every cycle, HTTP request, SQL lock, and SMTP handshake is instrumented under a strict **Zero-Crash** telemetry policy (`src/core/telemetry.py`), ensuring observability never breaks business delivery.

### 1. Application Metrics, Latency Spans (P50/P95) & Semantic `email.type` Breakdown

![Sentry Production Dashboard — Application Metrics, P50/P95 Latency & Email Types](./images/sentry_dashboard.png)

- **Real-Time Dispatch Counters (`sentry_sdk.metrics.count`)**:
 
- **Distributed Tracing & P50 / P95 Latency Percentiles**:

- **Semantic `email.type` Taxonomy (`EMAIL_TYPE_BY_TEMPLATE`)**:
  Every metric, `email.smtp.send` span, `smtp.retry` breadcrumb, and sanitized error scope carries an explicit `email.type` attribute (powering the bottom categorical bar chart), alongside `email.flow`, `email.stage`, `email.channel`, `email.dispatch_kind`, `email.recipient_domain`, and `smtp.account_slot`:

| Flow (`email.flow`) | Template (`email.template`) | Semantic Flag (`email.type`) | Trigger / Purpose |
| :--- | :--- | :--- | :--- |
| `order` | `pedido_aprovado` | `order_payment_confirmed` | Instant payment capture receipt (`STG 1`) |
| `order` | `pedido_pendente` | `order_payment_pending` | PIX / Boleto 5–30 min reminder (`STG 2`) |
| `order` | `pedido_a_caminho` | `order_shipped_tracking` | Carrier dispatch + tracking code (`STG 3`) |
| `order` | `cupom_pedido_1` | `order_recovery_coupon_10` | Unpaid order 24h recovery (10% OFF, `STG 5`) |
| `order` | `cupom_pedido_2` | `order_recovery_coupon_15` | Unpaid order 48h recovery (15% OFF, `STG 6`) |
| `order` | `cupom_pedido_3` | `order_recovery_coupon_20` | Unpaid order 72h recovery (20% OFF, `STG 7`) |
| `abandoned_cart` | `carrinho_abandonado_cupom4` | `cart_abandoned_reminder` | Initial cart abandonment 4h reminder (`STC 15`) |
| `abandoned_cart` | `carrinho_abandonado_cupom5` | `cart_recovery_coupon_1` | 1st cart recovery coupon at 24h (`STC 16`) |
| `abandoned_cart` | `carrinho_abandonado_cupom6` | `cart_recovery_coupon_2` | 2nd cart recovery coupon at 48h (`STC 17`) |

### 2. Autonomous Daemon Heartbeat & Crons Liveness (`yampi-daemon-cycle`)

![Sentry Crons Check-Ins — yampi-daemon-cycle](./images/crontab.png)

`src/daemon.py` wraps each execution cycle inside `sentry_sdk.crons.monitor`, emitting continuous `IN_PROGRESS` ➔ `OK` / `ERROR` check-ins to detect silent container hangs or crashed loops:
- **Monitor Slug:** `yampi-daemon-cycle` (`MACRO_SENTRY_CRON_MONITOR_SLUG`)
- **Schedule:** Interval every **5 minutes** (`MACRO_DAEMON_SLEEP_INTERVAL_SEG = 300`)
- **Operational Guardrails:** `checkin_margin: 2 min`, `max_runtime: 5 min`, `timezone: America/Sao_Paulo`, `failure_issue_threshold: 1` (alerts on first missed/failed check-in), and `recovery_threshold: 1` (auto-resolves on the next healthy cycle).

### 3. LGPD Compliance & Zero-PII Defense-in-Depth
- **SDK Scrubbing**: Initialized once via `_SENTRY_INITIALIZED` with `send_default_pii=False` (`src/core/logging_config.py`).
- **Deterministic Email Masking**: Logs mask customer addresses via `_mask_email()` (e.g., `lu***a@gmail.com`), while Sentry metrics only index the domain (`email.recipient_domain`).
- **Recursive Frame Sanitization**: `_build_pii_sanitizer_processor()` scrubs sensitive local variables (`email`, `raw_email`, `customer_data`, `order_data`, `cart_data`, `cpf`, `pix_code`, `html_body`, and auth/secret tokens) inside stacktrace `frame["vars"]` with `[REDACTED]` and sanitizes SMTP error codes (`535`, `550`) before transmission.

👉 **Full Telemetry & Dashboard Query Reference:** [`docs/sentry_dashboard_guide.md`](./docs/sentry_dashboard_guide.md)

---

## 🔒 Security & Pre-Release Governance

The codebase enforces automated pre-release security validation, credential hygiene, static code analysis, and container/dependency verification gates prior to deployment, backed by an automated test suite (**140 tests, 85%+ coverage**).

See [`SECURITY.md`](./SECURITY.md) for supported versions, data privacy safeguards, and private vulnerability reporting guidelines.

---

## ⚡ Quick Start & Deployment

> [!IMPORTANT]
> 📘 **Deploying to Production (Ubuntu 26.04.1 LTS)?**  
> Access the step-by-step production installation guide (`[PT-BR]`): **[`project_decisions/00_2_GUIA_DE_INSTALACAO_UBUNTU26.md`](./project_decisions/00_2_GUIA_DE_INSTALACAO_UBUNTU26.md)**  
> Review deployment architecture decisions and rationale (`[PT-BR]`): **[`project_decisions/00_DECISOES_DE_PROJETO_DEPLOY.md`](./project_decisions/00_DECISOES_DE_PROJETO_DEPLOY.md)**

**Prerequisites**: Docker & Docker Compose.

> [!IMPORTANT]
> By default, [`src/core/macros.py`](./src/core/macros.py) is configured for **production SMTP dispatch** (`MACRO_ENABLE_REAL_EMAIL_DISPATCH = True`, `MACRO_FORCE_TEST_EMAIL_RECIPIENT = False`, `MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH = False`, `MACRO_ENABLE_LOCAL_HTML_SAVING = False`). For local dry-run or staging tests, set `MACRO_ENABLE_REAL_EMAIL_DISPATCH = False` or `MACRO_FORCE_TEST_EMAIL_RECIPIENT = True` in `src/core/macros.py` before starting.
>
> **Modular Brand Images (`.env` + `assets/images/`):** Private brand images are **not** stored in the open-source repository. For production, copy your `images/` folder into `src/templates/emails/assets/images/` (or mount an external folder and set `EMAIL_ASSETS_DIR=/app/email_assets` in `.env`).

```bash
# 1. Clone the repository
git clone https://github.com/LucasDuarte026/message_integration_YAMPI.git
cd message_integration_YAMPI

# 2. Configure environment variables and attach modular brand images
cp .env.example .env
# Edit the .env file with your Yampi, Database, SMTP credentials, Sentry DSN, and EMAIL_ASSETS_DIR
# Copy your private brand images (optimized WebP assets) into: src/templates/emails/assets/images/

# 3. Launch the complete production stack via Makefile (App + DB)
make up

# 4. Stream real-time logs
make logs
```

<details>
<summary>🛠️ <b>View Available Makefile Commands (Click to expand)</b></summary>

| Command | Purpose |
| :--- | :--- |
| `make help` | Displays auto-documented CLI menu. |
| `make build` | Builds the Docker image tagged with `VERSION`. |
| `make up` | Starts all services (Postgres + Daemon) via Docker. |
| `make down` | Gracefully stops all containers. |
| `make logs` | Streams live logs from all containers. |
| `make restart` | Restarts the application stack (`down` followed by `up`). |
| `make sh` | Opens an interactive shell inside the `app` container. |
| `make run-all` | Executes carts and orders workers synchronously. |
| `make run-orders` | Runs the Orders worker (`STG`) in isolation. |
| `make run-carts` | Runs the Abandoned Carts worker (`STC`) in isolation. |
| `make db-query` | Runs interactive SQL queries against PostgreSQL. |
| `make db-find` | Finds database records by `order_id`, `cpf`, or `sku`. |
| `make db-del` | Deletes a record by ID/field from the control table. |
| `make db-search-orders` | Lists records with Orders state (`STG`). |
| `make db-search-carts` | Lists records with Abandoned Cart state (`STC`). |

</details>

---

## 📚 Technical Documentation & AI Agents

To modify workers, inspect state machine rules, or extend the autonomous ecosystem with AI agents, consult the detailed documentation:

👉 **[Read the Full Technical Documentation →](./docs/README.md)**  
👉 **[SDD Formal Specifications (EARS + Scenarios + ADRs) →](./docs/sdd_specs.md)**  
👉 **[Sentry Observability & Dashboard Guide →](./docs/sentry_dashboard_guide.md)**  
👉 **[Ubuntu 26.04.1 LTS Production Installation Guide (Page Zero) [PT-BR] →](./project_decisions/00_2_GUIA_DE_INSTALACAO_UBUNTU26.md)**  
👉 **[Deployment Architecture Decision Records (ADR) [PT-BR] →](./project_decisions/00_DECISOES_DE_PROJETO_DEPLOY.md)**

The architecture incorporates over 100 AI Agent skills under the `.agents/` directory, utilizing **Qdrant Vector Indexing** for cognitive integration into the development lifecycle.

---

## 📄 License and Commercial Use

This software is **proprietary**. Commercial use, modification, or distribution without explicit authorization is strictly prohibited. 

For commercial licensing and royalties inquiries, please refer to the project maintainers.

See the [LICENSE](./LICENSE) file for more details.
