# Message Integration Yampi 🚀

> **Automação inteligente de mensageria e recuperação de vendas para e-commerce (Yampi)**.

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-6.2.1-blue.svg)]()

## Why This Exists

Lojas virtuais perdem até **70% das vendas** no carrinho abandonado, e clientes frequentemente esquecem de pagar Pix e Boletos. Além disso, a falta de atualização sobre o rastreio sobrecarrega o suporte com mensagens do tipo *"onde está meu pedido?"*. 

O **Message Integration Yampi** resolve isso conectando-se diretamente à sua loja e disparando réguas de comunicação precisas via E-mail e WhatsApp, recuperando receita de forma silenciosa e automática.

## Quick Start

A maneira mais rápida de rodar o sistema e ver os disparos simulados rodando localmente na sua máquina:

```bash
git clone <repository_url>
cd message_integration
cp .env.example .env
```
*(Abra o arquivo `.env` e preencha suas chaves da Yampi e credenciais SMTP)*

```bash
docker compose up -d
docker compose logs -f app
```

## O Que a Ferramenta Faz?

1. **Recuperação de Carrinho Abandonado**: Disparo de cupons de incentivo dinâmicos (10%, 15% e 20%) respeitando janelas de tempo personalizadas.
2. **Incentivo de Pagamento Pendente (Pix/Boleto)**: Lembretes amigáveis com chave Pix e QR Code diretamente para o e-mail logo após a tentativa de compra.
3. **Confirmação e Rastreio**: Notificação imediata de pagamento aprovado e envio automatizado de código de rastreio (`on_carriage`).

## Como Usar (Regras de Disparo)

Por padrão, a ferramenta roda em **modo de segurança**: não gasta sua franquia de e-mails/WhatsApp e salva as mensagens HTML geradas na pasta local (`local_data/emails/`) para sua conferência.

Para habilitar disparos **reais** aos clientes, altere as macros em `src/core/macros.py`:
- `MACRO_ENABLE_REAL_EMAIL_DISPATCH = True`
- `MACRO_FORCE_TEST_EMAIL_RECIPIENT = False`

### Instalação Alternativa (Sem Docker)

**Prerequisites**: Python 3.10+

Para rodar localmente de forma nativa:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 src/daemon.py
```

## Documentação Técnica

Você é um desenvolvedor querendo entender a arquitetura, modificar os workers, ou ler as especificações da Máquina de Estados?

👉 **[Leia a Documentação Técnica Completa →](docs/README.md)**

## Licença e Uso Comercial

Este software é **proprietário**. O uso, modificação ou distribuição comercial sem autorização expressa é estritamente proibido. 

Para negociação de licenças comerciais e *royalties*, entre em contato via e-mail:
📧 `lucassalesduarte026@gmail.com`

Consulte o arquivo [LICENSE](LICENSE) para mais detalhes.
