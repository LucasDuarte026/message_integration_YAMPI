# Comprehensive Project Guide: Message Integration

## 1. Visão Geral (Overview)
Este projeto é um sistema de integração de mensagens projetado para atuar no ecossistema de e-commerce (especialmente integrado à plataforma Yampi). O objetivo primário é fornecer funcionalidades de reengajamento com clientes e comunicação de atualizações vitais, tais como recuperação de carrinhos abandonados e atualizações de status de pedidos.

O sistema foi concebido utilizando metodologias ágeis sólidas:
- **Spec-driven development (SDD)**: Onde as interfaces e contratos são definidos antes das implementações.
- **Test-driven development (TDD)**: Onde testes orientam a lógica.

Este documento serve como o "Manual do Usuário" e o "Manual do Desenvolvedor" consolidado, fornecendo uma visão ampla, não-técnica e técnica detalhada do projeto de ponta a ponta.

---

## 2. Casos de Uso (Use Cases)

### 2.1 Recuperação de Carrinho Abandonado (Abandoned Cart - Fluxo STC)
- **Problema:** Clientes adicionam produtos ao carrinho, mas saem antes de finalizar a compra.
- **Ação do Sistema:** O sistema consulta a API da Yampi regularmente buscando por carrinhos recém-abandonados (baseando-se em uma janela de horas específica). 
- **Verificação de Estado (STC):** Consulta o banco de dados unificado (`email_status_table`) verificando a coluna `stc` (Status Carrinho). Se `order_id` não for nulo (ou seja, já virou pedido), pula.
- **Execução:** Caso o `stc` permita (ex: transição null→15, 15→16, 16→17), despacha uma mensagem (via provedor SMTP/WhatsApp) contendo o cupom correspondente e o link `simulate_url` para incentivar o retorno à loja, avançando o estado da coluna `stc`.

### 2.2 Atualização de Pedidos (Orders Update - Fluxo STG)
- **Problema:** Clientes precisam estar informados do status de envio, ou serem incentivados a pagar (PIX/Boleto pendente), ou receber cupons de recuperação (pedido travado).
- **Ação do Sistema:** O sistema consulta pedidos recentes na API e avalia contra o estado local.
- **Verificação de Estado (STG):** Consulta a coluna `stg` (Status Global). Verifica a diferença de tempo (`diff`) desde a `data_pedido` ou status da Yampi.
- **Execução:** Dispara emails correspondentes à transição (ex: Email 1 para pagamento aprovado, Email 2 para incentivo ao PIX, ou Cupons 1, 2, 3 para pedidos não pagos após 24h, 48h, 72h) e avança a máquina de estados `stg`. Evita disparos nos estados terminais definidos pela [Lógica de E-mails](./email_state_machine.md).

---

## 3. Arquitetura e Fluxo (Lógica Sequencial)
A aplicação segue os princípios da **Clean Architecture** e **Hexagonal Architecture**. A regra de negócio principal nunca toca diretamente no banco de dados ou em bibliotecas de rede; ela interage com portas e adaptadores.

### A Lógica de Execução Sequencial
1. **Ponto de Entrada (Entrypoint):** 
   A aplicação é acionada através do `main.py` (para rotinas cron/agendadas) ou via `webhook_server.py` (para eventos em tempo real da Meta/Yampi).
   
2. **Injeção de Dependências:**
   No ponto de entrada, as credenciais são lidas (`core/config.py`). As conexões são estabelecidas (`core/client.py` para Yampi e `core/db.py` ou `ports/postgres_repo.py` para banco). Os provedores de envio são instanciados (`ports/whatsapp_meta_provider.py`, etc).

3. **Invocação dos Workers:**
   Todas as ferramentas instanciadas no passo anterior são injetadas num *Worker* de caso de uso (ex: `workers/abandoned_cart.py`).

4. **Processamento (Worker):**
   - **Consulta:** O Worker usa a interface injetada do cliente Yampi para pegar os dados puros.
   - **Lógica de Negócio:** Aplica filtros (tempo de abandono, tags, etc).
   - **Estado:** Verifica no Repositório de Estado se o evento já foi processado.
   - **Ação:** Chama o Provedor de Mensagem para enviar o texto.
   - **Confirmação:** Marca no Repositório de Estado que a tarefa foi concluída com sucesso para evitar disparos duplicados.

---

## 4. Quem Executa e Onde Consulta
- **Quem Executa (Regras de Negócio):** O diretório `src/workers/` possui os orquestradores (`AbandonedCartProcessor` e `OrderProcessor`). Eles são o "cérebro" das tarefas individuais, operando de forma concorrente via *ThreadPoolExecutor* para alta vazão.
- **Onde Consulta (Fonte de Dados):**
  - **Externa:** API da Yampi consumida via `src/core/client.py`.
  - **Interna (Estado):** Banco de Dados PostgreSQL unificado (`email_status_table` contendo `cart_id`, `order_id`, `order_number`, `stg`, `stc`, `data_pedido`, `data_carrinho`, `cpf`, `sku`) com suporte a travas de concorrência (`FOR UPDATE`), consultado via `src/ports/postgres_repo.py` para controle da máquina de estados dupla (STG para Pedidos e STC para Carrinhos).
- **O Que Fornece (Saída/Output):** 
  - Comunicações enviadas via provedores de mensagens implementados em `src/ports/` (ex: SMTP Email com TLS/SSL, WhatsApp Meta, Mocks para testes locais).

---

## 5. Decisões de Projeto

- **Infraestrutura Desacoplada:** Ao usar os contratos de `src/domain/interfaces.py`, o projeto pode trocar de provedor de mensagem (SMTP, Meta) alterando apenas a injeção no orquestrador principal sem que o Worker perceba.
- **Tolerância a Falhas e Duplicidade:** O uso estrito do banco de dados relacional atua como uma máquina de estados (STG/STC). As transações garantem que gargalos de API ou execuções paralelas de workers não gerem duplicidade ou *race conditions*.
- **Auto-documentação Estrita:** Exigência de que regras e contratos guiem o desenvolvimento. 
> [!CAUTION]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação no código-fonte, a documentação (tanto este overview geral quanto os READMEs marginais em `src/`) deve sofrer atualizações imediatas respectivas a essas mudanças para refletir o comportamento real do sistema em produção.

---

## 6. Logs e Depuração

### Fluxo de Logs
O sistema utiliza o módulo de logging nativo do Python configurado globalmente em [main.py](../src/main.py).
- **Destinos da Saída:** Console (`sys.stdout`) e arquivo em disco (`logs/app.log`).
- **Nível de Logs:** `INFO`.
- **Rastreamento de Regras:** O worker de carrinhos calcula e loga a idade de abandono em horas (`Analisando carrinho [id]: abandonado há [X.XX] horas. Regra aplicada: [fase]`), facilitando o rastreamento das regras aplicadas para cada fase de recuperação.

### Depuração Interativa e Execução Rápida
Para rastrear a execução linha por linha e acompanhar a pilha de chamadas e objetos (incluindo chamadas de funções filhas) de forma visual:
*   **Depurador em IDE (VS Code):** Configurado no arquivo [.vscode/launch.json](../.vscode/launch.json) para que o desenvolvedor possa colocar breakpoints no código e debugar de forma gráfica os comandos `abandoned-carts` e `orders` rodando localmente.
*   **Execução via Script:** Utilize o `./run_local.sh all` para executar a aplicação no terminal. Ele já carrega as variáveis do `.env`. Por padrão, roda em modo de teste (salvando os emails na pasta `emails/` e `tests/`). Adicione `--production` no final se quiser disparar emails reais.

### Mapeamento no Docker
Para persistência local e facilidade de depuração no ambiente host, o [docker-compose.yml](../docker-compose.yml) mapeia a pasta local `./logs_from_container` para `/app/logs` dentro do container da aplicação. Isso permite visualizar a execução em tempo real rodando comandos como `tail -f logs_from_container/app.log`.
