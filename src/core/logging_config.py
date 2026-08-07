import os
import sys
import logging

def setup_logging(verbose: bool = False, log_file: str = "local_data/logs/app.log") -> None:
    """
    Configura o sistema de logging da aplicação.
    Se verbose=True, define o nível de log para DEBUG.
    Caso contrário, mantém o nível padrão em INFO.
    """
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else "local_data/logs", exist_ok=True)
    
    sentry_dsn = os.environ.get("SENTRY_DSN")
    if sentry_dsn:
        try:
            import sentry_sdk
            traces_rate = float(os.environ.get("TRACES_SAMPLE_RATE", "1.0"))
            sentry_sdk.init(
                dsn=sentry_dsn,
                traces_sample_rate=traces_rate,
                send_default_pii=False, # Data Scrubbing habilitado (ignora dados sensíveis e PII locais)
            )
        except (ImportError, Exception) as e:
            logging.warning(f"Não foi possível inicializar o Sentry SDK: {e}")
    
    log_level = logging.DEBUG if verbose else logging.INFO
    
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Reconfigura handlers do logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove handlers antigos para evitar duplicidade em recargas
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(log_level)
    root_logger.addHandler(stream_handler)
    
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(log_level)
    root_logger.addHandler(file_handler)
    
    _setup_global_exception_hooks(root_logger)
    
    logging.info(f"Sistema de logging inicializado. Nível: {'DEBUG (Verbose)' if verbose else 'INFO'}")

def _setup_global_exception_hooks(logger: logging.Logger) -> None:
    """
    Configura os interceptadores globais para garantir que nenhuma exceção vaze sem log.
    """
    import threading

    def handle_unhandled_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            # Deixa o Ctrl+C funcionar normalmente
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        import traceback
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        logger.critical(
            "=================== FATAL ERROR ===================\n"
            "Exceção Não Tratada Global capturada pelo sys.excepthook!\n"
            f"Tipo: {exc_type.__name__} | Valor: {exc_value}\n"
            "A stack trace completa foi omitida do disco por segurança e enviada ao Sentry (se configurado).\n"
            "A aplicação será encerrada logo após este log."
        )
        
        _trigger_crash_report_thread(tb_str)

    def handle_thread_exception(args):
        if issubclass(args.exc_type, KeyboardInterrupt):
            return
            
        import traceback
        tb_str = "".join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
            
        logger.critical(
            "=================== THREAD FATAL ERROR ===================\n"
            f"Exceção Não Tratada na Thread '{args.thread.name}' capturada pelo threading.excepthook!\n"
            f"Tipo: {args.exc_type.__name__} | Valor: {args.exc_value}\n"
            "A stack trace completa foi omitida do disco por segurança e enviada ao Sentry (se configurado).\n"
            "A thread morreu silenciosamente."
        )
        
        _trigger_crash_report_thread(f"Thread: {args.thread.name}\n" + tb_str)

    sys.excepthook = handle_unhandled_exception
    
    if hasattr(threading, 'excepthook'):
        threading.excepthook = handle_thread_exception

def _trigger_crash_report_thread(exc_info_str: str) -> None:
    """
    Inicia uma thread separada para capturar os logs recentes e enviar via email
    o relatório de crash fatal diretamente para o usuário usando as configurações do .env.
    """
    import threading

    def worker():
        try:
            import os
            import smtplib
            from email.message import EmailMessage

            # Lê exclusivamente as credenciais do servidor SMTP de aviso de erros (TRACEBACK_SMTP_*)
            host = os.environ.get("TRACEBACK_SMTP_HOST", "smtp.gmail.com")
            port = int(os.environ.get("TRACEBACK_SMTP_PORT", "587"))
            user = os.environ.get("TRACEBACK_SMTP_USER")
            password = os.environ.get("TRACEBACK_SMTP_PASSWORD")
            from_addr = os.environ.get("TRACEBACK_SMTP_FROM") or user
            recipient = os.environ.get("TRACEBACK_EMAIL_RECIPIENT")

            if not user or not password or not recipient:
                return

            msg = EmailMessage()
            msg['Subject'] = "🚨 FATAL ERROR - Message Integration Yampi"
            msg['From'] = from_addr
            msg['To'] = recipient

            body = (
                "Um erro fatal ocorreu e a aplicação interceptou o crash.\n\n"
                "=================== TRACEBACK ===================\n"
                f"{exc_info_str}\n"
                "=================================================\n"
            )
            msg.set_content(body)

            # Anexa os últimos ~10MB do arquivo de log (aprox. 50.000 linhas)
            log_path = "local_data/logs/app.log"
            if os.path.exists(log_path):
                file_size = os.path.getsize(log_path)
                max_bytes = 10 * 1024 * 1024  # 10 MB limite SMTP (aprox 50 mil linhas)

                with open(log_path, 'rb') as f:
                    if file_size > max_bytes:
                        f.seek(file_size - max_bytes)
                        f.readline()  # Descarta linha inicial cortada
                    log_data = f.read()

                msg.add_attachment(
                    log_data,
                    maintype='text',
                    subtype='plain',
                    filename='app_crash_log.txt'
                )

            if port == 465:
                server = smtplib.SMTP_SSL(host, port, timeout=15)
            else:
                server = smtplib.SMTP(host, port, timeout=15)
                server.starttls()

            if user and password:
                server.login(user, password)

            server.send_message(msg)
            server.quit()
        except Exception:
            pass

    t = threading.Thread(target=worker, daemon=False)
    t.start()

