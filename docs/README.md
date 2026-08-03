# Reference: Message Integration Architecture

Welcome to the engineering documentation for the Message Integration Yampi project. This guide is built for developers who need to understand the underlying infrastructure, modify state machine behavior, or troubleshoot the running system.

## Explanation: Architecture & Component Boundaries

The project strictly follows **Clean Architecture (Hexagonal)**. Business rules are completely isolated from infrastructure (databases, APIs, Email).

- `src/core/`: Domain entities, global configurations (`config.py`), and fixed feature flags (`macros.py`).
- `src/domain/`: Use cases handling specific messaging logic (e.g., Abandoned Carts, Pending Orders).
- `src/ports/`: Interfaces for I/O operations (SQLite state persistence, Sentry telemetry, SMTP, Yampi API HTTP clients).
- `src/workers/`: Concurrent routines that periodically run Use Cases using `ThreadPoolExecutor`.
- `src/daemon.py`: The main orchestrator that manages thread lifecycles and timings.

## Explanation: The State Machine (STG / STC)

To prevent messaging loops, duplication, and spam, the system persists state in a local SQLite database (`state.db`).
Every Cart (STC) and Order (STG) moves through a strict lifecycle:

### Cart State Machine (STC)
- `STC1`: Triggered at 15 minutes (10% discount).
- `STC2`: Triggered at 24 hours (15% discount).
- `STC3`: Triggered at 72 hours (20% discount).

### Order State Machine (STG)
- `PIX_PENDING`: Triggered 30 minutes after order creation if unpaid.
- `PIX_APPROVED`: Triggered upon payment confirmation.
- `ON_CARRIAGE`: Triggered when package is dispatched, sending tracking info.

When an entity reaches a terminal state (e.g., cart converted, or 72h elapsed), it transitions to `completed` and is skipped in all future loops.

## Reference: Advanced Configuration (.env & Macros)

Dependency injection and feature flags are governed by your `.env` file and `macros.py`.

### Telemetry & Crash Reports (v6.2.1)
The daemon supports resilient crash reporting out of the box:
- `SENTRY_DSN`: Endpoint for Sentry error tracking. If left blank, it falls back to Email reporting.
- `TRACEBACK_SMTP_USER` / `PASSWORD`: Dedicated credentials for the system to email itself when a fatal crash occurs.
- `TRACEBACK_EMAIL_RECIPIENT`: The email address (usually the developer) that receives the stack trace and the tail of `app.log` (~50,000 lines, 10MB limit).

### HTTP Resilience & Auto-Retries (v6.3.0)
The `YampiClient` includes automatic transient network retry mechanisms:
- **Max Retries**: Performs up to 3 attempts with exponential backoff for transient connection resets (`ConnectionResetError`), network timeouts (`Timeout`), or HTTP 5xx server errors before raising an exception.
- **Fail-Fast**: Non-retryable client errors (HTTP 4xx like 401/404) raise immediately without retrying.

### Duplicate Supervision Email Dispatch (v6.3.0)
Allows production monitoring via real-time duplicate emails:
- **`MACRO_ENABLE_DUPLICATE_EMAIL_DISPATCH`**: When set to `True` in `macros.py`, every email dispatched to a real customer in production simultaneously triggers a duplicate copy sent to `TEST_EMAIL_RECIPIENT` (`deutschlucas026@gmail.com`) for real-time audit.

## Tutorial: How to Run the Test Suite

Before committing any modifications, ensure the core logic remains intact by running the unit tests:

```bash
# Activate your virtual environment
source venv/bin/activate

# Discover and run all unit tests
python3 -m unittest discover -s tests
```

## Visual Diagrams

For visual reference of how components talk to each other, see the Mermaid diagrams below:

* 🏛️ [System Architecture & Clean Layers](./architecture.md)
* 💻 [Hardware Specifications & Resource Limits (Benchmarking)](./architecture.md#-especificação-de-hardware-e-dimensionamento-benchmarking)
* ⚙️ [State Machine Temporal Rules](./email_state_machine.md)
* 📊 [Orders State Diagram (STG)](./diagramas/stateDiagramOrders.md)
* 📊 [Abandoned Carts State Diagram (STC)](./diagramas/stateDiagramAbandonedCarts.md)

---
*For business features and licensing inquiries, refer back to the [Main README](../README.md).*

