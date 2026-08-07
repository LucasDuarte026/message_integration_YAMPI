# Diretrizes e Arquitetura de Testes (Pytest)

Este documento define a padronização oficial de testes do projeto, adotada a partir de agosto de 2026, utilizando o **Pytest** como motor central.

## 1. Princípios (Test-Driven Development)
Todo novo código ou correção de bug deve ser acompanhado de testes. Siga o fluxo TDD:
1. **Red:** Escreva o teste reproduzindo o bug ou a funcionalidade desejada. O teste deve falhar.
2. **Green:** Escreva a quantidade mínima de código de produção para o teste passar.
3. **Refactor:** Limpe o código, garanta a performance e aplique as regras arquiteturais, mantendo os testes verdes.

## 2. Estrutura do Diretório de Testes
Todos os testes devem residir na pasta `tests/` e obedecer à seguinte hierarquia:

```text
tests/
├── conftest.py             # Fixtures globais compartilhadas. NUNCA importe este arquivo diretamente.
├── unit/                   # Testes unitários puros (rápidos, isolados, mocks de I/O).
│   ├── test_client.py
│   └── ...
└── integration/            # Testes de integração (batem no DB real, APIs via VCR.py, fluxos ponta-a-ponta).
    ├── test_abandoned_cart.py
    └── ...
```

## 3. O Ecossistema Pytest

O projeto utiliza as seguintes bibliotecas:
- `pytest`: Motor de testes.
- `pytest-mock`: Para manipulação elegante de injeção de dependências (substitui o `unittest.mock.patch`).
- `pytest-cov`: Para análise de cobertura de código.

### Comando Padrão de Execução
Para executar a suite completa, partindo da raiz do projeto:
```bash
PYTHONPATH=. pytest tests/
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
