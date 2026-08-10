from datetime import datetime, timezone
from zoneinfo import ZoneInfo

def get_now_utc() -> datetime:
    """
    Retorna o horário atual timezone-aware em UTC.
    Utilizado como padrão absoluto para cálculos de negócio e armazenamento.
    """
    return datetime.now(timezone.utc)

def parse_yampi_date_to_utc(date_payload: dict | str | None) -> datetime:
    """
    Parseia estritamente um payload de data da Yampi.
    O payload deve ser um dicionário contendo 'date' e 'timezone'.
    Se a informação de fuso horário estiver ausente, levanta ValueError.
    Retorna o objeto datetime no fuso UTC.
    """
    if not isinstance(date_payload, dict):
        raise ValueError(f"Payload de data da Yampi inválido. Esperado dict, recebido: {type(date_payload)}")
    
    date_str = date_payload.get("date")
    tz_str = date_payload.get("timezone")
    
    if not date_str or not tz_str:
        raise ValueError("Payload de data da Yampi ausente ou sem timezone (faltam campos 'date' ou 'timezone').")
    
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            raise ValueError(f"Formato de data '{date_str}' não reconhecido.") from e

    try:
        dt = dt.replace(tzinfo=ZoneInfo(tz_str))
    except Exception as e:
        raise ValueError(f"Timezone '{tz_str}' inválido ou não reconhecido pelo Python.") from e

    return dt.astimezone(timezone.utc)

def to_local_sp(dt: datetime) -> datetime:
    """
    Recebe um datetime UTC (ou outro aware) e converte de volta para o fuso horário de SP.
    Ideal para uso puramente estético na camada de apresentação (Logs e E-mails).
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(ZoneInfo("America/Sao_Paulo"))
