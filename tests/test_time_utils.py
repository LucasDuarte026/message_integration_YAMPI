import pytest
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from src.core.time_utils import parse_yampi_date_to_utc

def test_parse_yampi_valid_sao_paulo():
    """Testa se um payload válido de SP é convertido corretamente para UTC."""
    payload = {
        "date": "2026-08-09 21:37:38.000000",
        "timezone_type": 3,
        "timezone": "America/Sao_Paulo"
    }
    dt_utc = parse_yampi_date_to_utc(payload)
    
    # 21:37:38 em SP (UTC-3) é 00:37:38 do dia seguinte em UTC
    assert dt_utc.tzinfo == timezone.utc
    assert dt_utc.year == 2026
    assert dt_utc.month == 8
    assert dt_utc.day == 10
    assert dt_utc.hour == 0
    assert dt_utc.minute == 37
    assert dt_utc.second == 38

def test_parse_yampi_missing_timezone():
    """Testa falha se a Yampi parar de mandar o timezone (Fail-Fast)."""
    payload = {
        "date": "2026-08-09 21:37:38.000000"
    }
    with pytest.raises(ValueError, match="ausente ou sem timezone"):
        parse_yampi_date_to_utc(payload)

def test_parse_yampi_invalid_type():
    """Testa falha se o payload for uma string plana em vez de dict."""
    payload = "2026-08-09 21:37:38.000000"
    with pytest.raises(ValueError, match="Esperado dict, recebido: <class 'str'>"):
        parse_yampi_date_to_utc(payload) # type: ignore

def test_parse_yampi_invalid_timezone():
    """Testa falha se o timezone não existir no banco IANA."""
    payload = {
        "date": "2026-08-09 21:37:38.000000",
        "timezone": "Planeta/Marte"
    }
    with pytest.raises(ValueError, match="inválido ou não reconhecido pelo Python"):
        parse_yampi_date_to_utc(payload)

def test_parse_yampi_valid_no_microseconds():
    """Testa leitura de data válida sem os milissegundos."""
    payload = {
        "date": "2026-08-09 21:37:38",
        "timezone": "America/Sao_Paulo"
    }
    dt_utc = parse_yampi_date_to_utc(payload)
    assert dt_utc.tzinfo == timezone.utc
    assert dt_utc.hour == 0
