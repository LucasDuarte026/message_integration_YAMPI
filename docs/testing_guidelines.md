# Diretrizes e Arquitetura de Testes (Pytest)

Este documento define a padronização oficial de testes do projeto, adotada a partir de agosto de 2026, utilizando o **Pytest** como motor central.

## 1. Princípios (Test-Driven Development)
Todo novo código ou correção de bug deve ser acompanhado de testes. Siga o fluxo TDD:
1. **Red:** Escreva o teste reproduzindo o bug ou a funcionalidade desejada. O teste deve falhar.
2. **Green:** Escreva a quantidade mínima de código de produção para o teste passar.
3. **Refactor:** Limpe o código, garanta a performance e aplique as regras arquiteturais, mantendo os testes verdes.

## 2. Estrutura do Diretório de Testes
Todos os testes residem na pasta `tests/` com suítes focadas por módulo e mocks/fixtures compartilhados:

```text
tests/
├── conftest.py                  # Fixtures globais compartilhadas e env vars de teste.
├── carts_mock.json              # Payloads simulados de carrinhos Yampi.
├── orders_mock.json             # Payloads simulados de pedidos Yampi.
├── test_abandoned_cart.py       # Fluxo STC, âncora updated_at/DB UTC e rollback fail-safe.
├── test_orders.py               # Fluxo STG, rastreio obrigatório, âncora created_at/DB UTC.
├── test_postgres_repo_pool.py   # Pool, COALESCE(LEAST(...)), update_stg/stc e falhas SQL.
├── test_smtp_email_provider.py  # Mascaramento LGPD, CID inline, WebP/assets_dir, retries e close().
├── test_email_plain_text.py     # Geração da alternativa text/plain (RFC 2046) no BaseEmailBuilder.
├── test_dual_sender_routing.py  # Roteamento dual (oficial@ vs comercial@), fallback e concorrência.
├── test_email_telemetry.py      # Contadores Sentry, isolamento ThreadPoolExecutor, traceback e LGPD.
├── test_logging_config.py       # Criação de pastas e SafeRotatingFileHandler.
├── test_main_and_daemon.py      # Orquestração, _close_resources, Sentry idempotente, builders e webhook.
├── test_client.py               # Cliente HTTP Yampi.
├── test_customer_extraction.py  # Extração defensiva de dados do cliente.
└── test_time_utils.py           # Arquitetura UTC-First e rejeição Fail-Fast de datas naive.
```

> **Estado Atual da Suíte:** **107 testes e 7 subtestes passando** com **85% de cobertura global em `src/`** (sendo 88% em `src/core/telemetry.py`, 96% em `src/ports/smtp_email_provider.py` e 95% em `src/services/notification_service.py`).

## 3. O Ecossistema Pytest

O projeto utiliza as seguintes bibliotecas (registradas em `requirements.txt`):
- `pytest`: Motor de testes.
- `pytest-mock`: Para manipulação de mocks sem vazamento de estado.
- `pytest-cov`: Para análise de cobertura de código.

### Comando Padrão de Execução
Para executar a suíte completa com cobertura de `src/`, partindo da raiz do projeto:
```bash
.venv/bin/python -m pytest --cov=src --cov-report=term-missing
```

## 4. Melhores Práticas

### 4.1. Fixtures e Injeção de Dependências
Nunca utilize `setUp` ou `tearDown` do `unittest`. Utilize *Fixtures* do Pytest.
Fixtures que serão usadas por mais de um arquivo de teste devem ser declaradas em `tests/conftest.py`.

```python
# Em conftest.py
import pytest

@pytest.fixture
def mock_yampi_payload():
    return {"data": [{"id": 123, "status": "paid"}]}

# No arquivo de teste (test_algo.py)
# Pytest injeta o payload automaticamente pelo nome do argumento!
def test_processamento_yampi(mock_yampi_payload):
    resultado = processar(mock_yampi_payload)
    assert resultado is True
```

### 4.2. Mocks com `pytest-mock`
Utilize a fixture nativa `mocker` para substituir comportamentos, em vez de usar decoradores `@patch`. Isso garante que o mock não vaze o estado de forma global caso o teste falhe abruptamente.

```python
def test_envio_email_falha_de_rede(mocker):
    # Substitui a função send_email pelo mock
    mock_send = mocker.patch("src.ports.smtp_email_provider.SmtpEmailProvider.send_email")
    mock_send.side_effect = ConnectionError("SMTP down")
    
    # Chama a rotina
    with pytest.raises(ConnectionError):
        enviar_notificacao("123")
```

### 4.3. Parametrização
Evite copiar e colar testes inteiros só para mudar um input. Use `@pytest.mark.parametrize`:

```python
import pytest

@pytest.mark.parametrize("status_pedido, status_esperado", [
    ("on_carriage", 3),
    ("paid", 2),
    ("canceled", None)
])
def test_mapeamento_status(status_pedido, status_esperado):
    resultado = mapear_status(status_pedido)
    assert resultado == status_esperado
```

### 4.4. Cobertura de Caminhos de Sucesso e Falha (Try/Except)
**Regra Estrita:** Sempre que houver validações, processamentos ou fluxos envolvidos em blocos `try/except` (como a extração de dados sensíveis ou conversores), você é **obrigado** a testar exaustivamente o caminho feliz (sucesso) E garantir testes para os caminhos de erro que forçam a subida da exceção (`raise` ou captura do erro pelo log).
Isso garante a confiabilidade da nossa arquitetura *Fail-Fast*, assegurando que o erro correto suba nas condições corretas e o sistema não processe dados corrompidos de forma silenciosa. Use o `with pytest.raises(...)` para validar a ocorrência exata da exceção.
