# 🚀 Message Integration Yampi

[![Release Status](https://img.shields.io/badge/Release-v7.1.1%20STABLE-success?style=for-the-badge&logo=rocket)](https://github.com/LucasDuarte026/message_integration_YAMPI/releases)
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

According to the **[Baymard Institute](https://baymard.com/lists/cart-abandonment-rate)** (meta-analysis of 50 global e-commerce usability studies), online stores lose an average of **70.19% of checkout traffic to cart abandonment** (rising past **75%+ on mobile**), while also suffering from expired PIX/bank slip payments due to a lack of immediate, intelligent re-engagement. Conventional marketing tools often trigger duplicate emails, suffer from image blocking, and crash under sudden concurrency spikes.

**Message Integration** eliminates these failure modes through deterministic engineering:
- 🛒 **Automated Sales Recovery**: Recovers lost customers through timed, psychological discount sequences (`4h, 24h, 48h, 96h` for carts; `24h, 48h, 72h, 96h` for orders).
- ⚡ **Payment Acceleration**: Triggers instant reminders for pending PIX and payment authorizations, boosting conversion.
- 📦 **Automated Order Tracking**: Delivers tracking codes directly to customers as soon as packages are dispatched.
- 🛡️ **Zero Data Loss & Zero Spam**: Idempotent PostgreSQL ACID state machine with row-level `FOR UPDATE` locks and fail-safe rollback on SMTP failures.

---

## 📊 Business Impact & Industry Benchmarks

> Industry baseline figures below are sourced directly from **[Baymard Institute](https://baymard.com/lists/cart-abandonment-rate)** (checkout abandonment), **[Klaviyo Abandoned Cart Benchmarks](https://www.klaviyo.com/blog/abandoned-cart-benchmarks)** (recovery sequences), **[Validity Email Deliverability Benchmark Report](https://www.validity.com/resource-center/email-deliverability-benchmark-report/)** (global inbox placement), and **[Gorgias WISMO Research](https://www.gorgias.com/blog/wismo)** (post-purchase support load), paired with this repository's audited telemetry and anti-spam metrics.

| Dimension | Industry Baseline (Cited Source) | With Message Integration (Audited) | Direct Engineering & Business Outcome |
| :--- | :---: | :---: | :--- |
| **Checkout Abandonment** | **70.19% Abandoned** ([Baymard Institute](https://baymard.com/lists/cart-abandonment-rate)) | **Multi-Stage Recovery (`4h, 24h, 48h, 96h`)** | 📈 Automated progressive coupon sequences (`10% ➔ 15% ➔ 20%`) aligned with [Klaviyo Benchmarks](https://www.klaviyo.com/blog/abandoned-cart-benchmarks) |
| **Email Deliverability (Inbox)** | **~85% Global Inbox Rate** ([Validity Report](https://www.validity.com/resource-center/email-deliverability-benchmark-report/)) | **`10/10` Mail-Tester (`-0.2` SpamAssassin)** | 🎨 `SPF -all`, `2048-bit DKIM`, `DMARC p=quarantine`, RFC 5322/2046/8058 & Google Postmaster Compliant |
| **Customer Support (*WISMO*)** | **30% – 50% of Support Tickets** ([Gorgias Research](https://www.gorgias.com/blog/wismo)) | **Automated `STG 3` Carrier Tracking** | 📦 Proactive dispatch & tracking-code alerts reducing *"Where is my order?"* inquiries |
| **Dispatch & Runtime Stability** | Vulnerable to SMTP drops & API timeouts | **`100%` Verified Delivery (`49/49` Sentry APM)** | 🛡️ PostgreSQL ACID row locks (`FOR UPDATE`), exponential backoff & zero memory leaks (95-min stress test) |

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
  - `email.dispatch.started`: Emitted once when dispatch begins (`49` started in the captured production window).
  - `email.dispatch.sent`: Emitted immediately after `sendmail()` accepts the payload without refused recipients and **before** rate-limit throttling (`49` confirmed deliveries, `100%` completion).
  - `email.dispatch.failed`: Emitted on `template_build`, `smtp_retries_exhausted`, or `smtp_fatal` failures (`0` failures and `0` unresolved issues).
- **Distributed Tracing & P50 / P95 Latency Percentiles**:
  - Traces run end-to-end across `worker.process` ➔ `http.client` (Yampi REST API) ➔ `db.sql.query` (PostgreSQL Pool) ➔ `email.smtp.send` (Authenticated SMTP Relay).
  - **P50 (Median)** tracks typical execution latency (`3.76s` per worker cycle; `102.63ms` average across `7.1K` I/O spans).
  - **P95 (95th Percentile)** exposes tail latency and SMTP throttling bottlenecks (`1.05min` for heavy batch cycles; `118.88ms` across I/O spans) before timeouts occur.
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
