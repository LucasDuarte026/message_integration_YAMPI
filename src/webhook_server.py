import os
from flask import Flask, request
from src.core.macros import MACRO_META_WEBHOOK_VERIFY_TOKEN, MACRO_WEBHOOK_SERVER_PORT

sentry_dsn = os.environ.get("SENTRY_DSN")
if sentry_dsn:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        traces_rate = float(os.environ.get("TRACES_SAMPLE_RATE", "1.0"))
        env_name = os.environ.get("ENVIRONMENT", "production")
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[FlaskIntegration()],
            traces_sample_rate=traces_rate,
            environment=env_name,
            send_default_pii=False,
        )
    except Exception as e:
        print(f"Não foi possível inicializar o Sentry no Webhook Server: {e}")

app = Flask(__name__)

# Token de verificação que você digitará no painel da Meta
VERIFY_TOKEN = MACRO_META_WEBHOOK_VERIFY_TOKEN

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    """
    Endpoint principal para receber eventos e validações de Webhook da Meta API.
    """
    # 1. Validação exigida pela Meta no momento de cadastrar o Webhook (GET)
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("\n[INFO] Webhook verificado com sucesso pela Meta!")
            return challenge, 200
        else:
            print("\n[WARNING] Falha na verificação: tokens não coincidem.")
            return "Forbidden", 403
            
    # 2. Recebimento dos eventos de mensagem e atualizações de status (POST)
    elif request.method == "POST":
        data = request.json
        print("\n[INFO] Evento do WhatsApp recebido:")
        
        # Estrutura básica para logar os dados principais no terminal
        try:
            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Se for uma mensagem recebida do cliente
            if "messages" in value:
                message = value["messages"][0]
                sender = message.get("from")
                text = message.get("text", {}).get("body", "[Mensagem sem texto]")
                print(f"-> Mensagem de {sender}: '{text}'")
                
            # Se for uma atualização de status (sent, delivered, read, failed)
            elif "statuses" in value:
                status = value["statuses"][0]
                recipient = status.get("recipient_id")
                status_type = status.get("status")
                print(f"-> Status do envio para {recipient}: '{status_type}'")
                
        except Exception as e:
            # Caso o payload mude, loga o JSON completo para análise
            print(f"Erro ao extrair dados do payload: {e}")
            print(data)

        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    print(f"Iniciando servidor de Webhook local na porta {MACRO_WEBHOOK_SERVER_PORT}...")
    print(f"Configure o token de verificação na Meta como: '{VERIFY_TOKEN}'")
    app.run(port=MACRO_WEBHOOK_SERVER_PORT)
