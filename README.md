# Message Integration Yampi 🚀

> **Automação inteligente de mensageria e recuperação de vendas para e-commerce (Yampi)**.

---

## 📌 O que é o projeto?

O **Message Integration** é uma solução automatizada projetada para e-commerces integrados à plataforma **Yampi**. O sistema monitora constantemente os carrinhos abandonados e a atualização de pedidos, orquestrando réguas de comunicação personalizadas via **E-mail** e **WhatsApp**.

Sua missão é engajar o cliente no momento certo — desde a recuperação de um carrinho esquecido até o envio automático do código de rastreio após o despacho da compra.

---

## 💡 A Dor que o Projeto Resolve

### 🚨 O Problema: Perda Silenciosa de Receita
Em lojas virtuais, até **70% dos carrinhos criados são abandonados** antes da finalização do pagamento. Além disso:
- Clientes que geram Pix ou Boleto frequentemente se esquecem de efetuar o pagamento antes do vencimento.
- A falta de atualização transparente sobre o envio do pacote gera ansiedade no cliente e sobrecarrega a equipe de suporte com perguntas do tipo *"Onde está meu pedido?"*.

### ⚡ A Solução: Comunicação Reativa e Automatizada
O **Message Integration** resolve essa dor através de uma **máquina de estados inteligente** que acompanha o ciclo de vida de cada carrinho e pedido:

1. **Recuperação de Carrinho Abandonado**: Disparo de cupons de incentivo dinâmicos (10%, 15% e 20%) respeitando janelas de tempo personalizadas.
2. **Incentivo de Pagamento Pendente (Pix/Boleto)**: Lembretes amigáveis com chave Pix e QR Code direto no e-mail logo após a tentativa de compra.
3. **Confirmação e Rastreio**: Notificação imediata de pagamento aprovado e envio automatizado do e-mail com código de rastreio assim que o pedido é despachado na Yampi (`on_carriage`).
4. **Sem Spam ou Duplicidade**: Sistema de persistência transacional que garante que cada mensagem seja enviada exatamente uma única vez por estágio.

---

## 📊 Métricas e Resultados Esperados

O projeto foi desenhado para gerar impacto direto nos indicadores essenciais da operação de e-commerce:

| Indicador (KPI) | Objetivo da Solução | Impacto na Operação |
| :--- | :--- | :--- |
| **Taxa de Conversão de Carrinhos** | Resgatar vendas abandonadas via cupons progressivos | 📈 Aumento no faturamento direto |
| **Recuperação de Pix/Boleto Pendente** | Lembrar o cliente nas primeiras horas após o pedido | ⏱️ Redução de pedidos cancelados por expiração |
| **Satisfação do Cliente (NPS/CSAT)** | Transparência com e-mails de confirmação e rastreio | 🚚 Melhor experiência de pós-venda |
| **Carga de Chamados de Suporte** | Envio proativo do código e link de acompanhamento | 📉 Queda drástica em perguntas sobre rastreamento |

*(Métricas numéricas reais de produção serão consolidadas nesta seção conforme o histórico de campanhas).*

---

## 🚀 Como Usar

### 1. Pré-requisitos e Configuração

Crie o arquivo `.env` na raiz do projeto preenchendo as credenciais da API da Yampi:

```bash
cp .env.example .env
```

**Variáveis Principais (`.env`):**
* `YAMPI_USER_TOKEN`: Seu token de usuário da Yampi.
* `YAMPI_USER_SECRET_KEY`: Sua chave secreta da Yampi.
* `YAMPI_ALIAS`: Alias da sua loja (opcional, detectado automaticamente).

---

### 2. Execução com Docker (Recomendado) 🐳

Suba os serviços com Docker Compose:

```bash
docker compose up -d
```

#### Exemplos de Comandos (CLI):

```bash
# Processar recuperação de pedidos (Orders Worker)
docker compose exec app python src/main.py orders

# Processar carrinhos abandonados (Dry-Run / Simulado)
docker compose exec app python src/main.py abandoned-carts

# Processar em ambiente de Produção (Envio real via SMTP)
docker compose exec app python src/main.py abandoned-carts --production
```

---

### 3. Execução Nativa (Python Local)

```bash
# Rodar o orquestrador completo em modo simulado (Dry-Run)
./run_local.sh all

# Executar/Buscar apenas Pedidos (STG)
./db_consult_scripts/run_stg.sh           # Modo simulado (Dry-Run)
./db_consult_scripts/run_stg.sh --production # Modo produção

# Executar/Buscar apenas Carrinhos Abandonados (STC)
./db_consult_scripts/run_stc.sh           # Modo simulado (Dry-Run)
./db_consult_scripts/run_stc.sh --production # Modo produção

# Consultar o banco de dados por status STG ou STC
./db_consult_scripts/search_stg.sh        # Lista todos os registros com estado STG
./db_consult_scripts/search_stg.sh 2      # Lista registros com STG = 2 (Incentivo PIX)
./db_consult_scripts/search_stc.sh 15     # Lista registros com STC = 15 (Cupom 4)
```

> **Dica**: No modo Dry-Run, o sistema não gasta créditos de mensagens e salva o HTML do e-mail em `emails/` para conferência visual.

---

## 🛠️ Testes e Auditoria

```bash
# Executar a suíte de testes unitários
python3 -m unittest discover -s tests

# Visualizar logs em tempo real
tail -f logs/app.log
```

---

## 📚 Documentação Técnica Aprofundada

Para desenvolvedores e arquitetos que desejam entender os detalhes internos, especificações e arquitetura do projeto:

* 🏛️ **[Arquitetura do Sistema e Estrutura de Diretórios](./docs/architecture.md)** — Camadas Clean/Hexagonal e mapa visual de arquivos.
* ⚙️ **[Máquina de Estados (STG/STC)](./docs/email_state_machine.md)** — Regras de transição, temporizadores e esquema de dados.
* 📊 **[Diagramas de Estados](./docs/diagramas/README.md)** — Diagramas Mermaid visuais dos fluxos de [Pedidos (STG)](./docs/diagramas/stateDiagramOrders.md) e [Carrinhos Abandonados (STC)](./docs/diagramas/stateDiagramAbandonedCarts.md).
* 📋 **[Histórico de Alterações](./CHANGELOG.md)** — Registro detalhado de versões e releases.
* 🔮 **[Roadmap de Implementações](./docs/future_implementations.md)** — Próximos passos e melhorias futuras.
