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
- **Verificação de Estado (STC):** Consulta o banco de dados unificado (`email_status_table`) verificando a coluna `stc` (Status Carrinho). Se `order_id` não for nulo (ou seja, já virou pedido), pula (consulte o [Diagrama de Estados do Carrinho - STC](./diagramas/stateDiagramAbandonedCarts.md)).
- **Execução:** Caso o `stc` permita (ex: transição null→15, 15→16, 16→17), despacha uma mensagem (via provedor SMTP/WhatsApp) contendo o cupom correspondente e o link `simulate_url` para incentivar o retorno à loja, avançando o estado da coluna `stc`.

### 2.2 Atualização de Pedidos (Orders Update - Fluxo STG)
- **Problema:** Clientes precisam estar informados do status de envio, ou serem incentivados a pagar (PIX/Boleto pendente), ou receber cupons de recuperação (pedido travado).
- **Ação do Sistema:** O sistema consulta pedidos recentes na API e avalia contra o estado local.
- **Verificação de Estado (STG):** Consulta a coluna `stg` (Status Global). Verifica a diferença de tempo (`diff`) desde a `data_pedido` ou status da Yampi (consulte o [Diagrama de Estados de Pedidos - STG](./diagramas/stateDiagramOrders.md)).
- **Execução:** Dispara emails correspondentes à transição (ex: Email 1 para pagamento aprovado, Email 2 para incentivo ao PIX, ou Cupons 1, 2, 3 para pedidos não pagos após 24h, 48h, 72h) e avança a máquina de estados `stg`. Evita disparos nos estados terminais definidos pela [Lógica de E-mails](./email_state_machine.md) e visualizados no [Índice de Diagramas](./diagramas/README.md).

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

### Fluxo de Logs e Tratamento Global de Erros
O sistema utiliza o módulo de logging nativo do Python configurado globalmente em [logging_config.py](../src/core/logging_config.py).
- **Destinos da Saída:** Console (`sys.stdout`) e arquivo em disco (`logs/app.log`).
- **Nível de Logs:** `INFO` por padrão (ou `DEBUG` com a flag `-v`).
- **Interceptação Global e Notificação Reativa (Thread & Sentry):** O sistema substitui o comportamento padrão do Python instalando `sys.excepthook` e `threading.excepthook`. Qualquer exceção inesperada ou erro fatal é capturado e registrado como `FATAL ERROR`. O sistema ativa uma thread em background que envia um e-mail de alerta para o mantenedor via servidor `TRACEBACK_SMTP_*` contendo o traceback completo e os últimos 10MB (~50.000 linhas) do arquivo de log em anexo. Paralelamente, envia os eventos de erro para o **Sentry SDK** (`SENTRY_DSN`) com *Data Scrubbing* ativado.
- **Rastreamento de Regras:** Os workers calculam e logam a idade de abandono em horas (`Analisando carrinho [id]: abandonado há [X.XX] horas. Regra aplicada: [fase]`), facilitando o rastreamento das regras aplicadas.

### Depuração Interativa e Execução Rápida
Para rastrear a execução linha por linha e acompanhar a pilha de chamadas e objetos (incluindo chamadas de funções filhas) de forma visual:
*   **Depurador em IDE (VS Code):** Configurado no arquivo [.vscode/launch.json](../.vscode/launch.json) para que o desenvolvedor possa colocar breakpoints no código e debugar de forma gráfica os comandos `abandoned-carts` e `orders` rodando localmente.
*   **Execução contínua (Daemon):** O orquestrador oficial de execução contínua é o arquivo `src/daemon.py`. Todas as flags de disparo ou modo de simulação devem ser configuradas via código em `src/core/macros.py`.
*   **Mapeamento no Docker:**
Para persistência local e facilidade de depuração no ambiente host, o [docker-compose.yml](../docker-compose.yml) mapeia a pasta local `./local_data/logs` para `/app/local_data/logs` dentro do container da aplicação. Isso permite visualizar a execução em tempo real rodando comandos como `tail -f local_data/logs/app.log`.

---

## 7. Configuração Detalhada e Variáveis de Ambiente (`.env`)

O arquivo [config.py](../src/core/config.py) carrega as configurações da aplicação com base nas variáveis de ambiente. Defina-as no terminal antes da execução ou crie um arquivo `.env`:

| Variável | Descrição | Padrão | Obrigatória? |
| :--- | :--- | :--- | :--- |
| `YAMPI_USER_TOKEN` | Token do usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_USER_SECRET_KEY` | Chave secreta de usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_ALIAS` | Alias da sua loja Yampi (opcional; detectado automaticamente se omitido). | - | Não |
| `SQLITE_DB_PATH` | Caminho do arquivo SQLite para persistir estados locais em dev. | `state.db` | Não |
| `POSTGRES_HOST` / `POSTGRES_DB` | Conexão com o banco PostgreSQL de produção. | `localhost` | **Sim (Produção)** |
| `TEST_EMAIL_RECIPIENT` | E-mail de destino para envio em modo de teste/homologação. | `wpplucas026@gmail.com` | Não |
| `MAX_CART_AGE_HOURS` | Limite de tempo em horas (cutoff) para desconsiderar carrinhos muito antigos. | `48` | Não |
| `MAX_WORKERS` | Quantidade máxima de threads paralelas para processamento. | `10` | Não |
| **SMTP Configs (Clientes)** | | | |
| `SMTP_USER` | Usuário de autenticação do servidor SMTP principal. | - | **Sim (Modo Produção)** |
| `SMTP_PASSWORD` | Senha ou Token de App do e-mail SMTP. | - | **Sim (Modo Produção)** |
| `SMTP_HOST` | Host do servidor de e-mail. | `smtp.gmail.com` | Não |
| `SMTP_PORT` | Porta do servidor SMTP (usar `465` para SSL ou `587` para TLS). | `587` | Não |
| `SMTP_FROM` | E-mail remetente que aparecerá no cabeçalho dos clientes. | `SMTP_USER` | Não |
| **Traceback SMTP Configs (Alertas de Erros)** | | | |
| `TRACEBACK_SMTP_USER` | Usuário SMTP exclusivo para alertas de exceção. | - | Não |
| `TRACEBACK_SMTP_PASSWORD` | Senha/Token SMTP exclusivo para alertas. | - | Não |
| `TRACEBACK_SMTP_HOST` | Host SMTP para alertas de exceção. | `smtp.gmail.com` | Não |
| `TRACEBACK_SMTP_PORT` | Porta SMTP para alertas. | `587` | Não |
| `TRACEBACK_SMTP_FROM` | E-mail remetente do alerta. | `TRACEBACK_SMTP_USER` | Não |
| `TRACEBACK_EMAIL_RECIPIENT` | E-mail de destino (mantenedor) que receberá o aviso de crash com o log. | - | Não |
| **Sentry Configs** | | | |
| `SENTRY_DSN` | DSN do projeto no Sentry para monitoramento em nuvem. | - | Não |
| **Meta WhatsApp Configs** | | | |
| `META_WA_TOKEN` | Token temporário ou permanente da Meta Cloud API. | - | Não |
| `META_PHONE_NUMBER_ID` | Identificador de número de telefone gerado na Meta Cloud API. | - | Não |
| `META_WA_TEMPLATE_NAME`| Nome do template homologado no painel da Meta. | `hello_world` | Não |
| `META_WA_TEMPLATE_LANG`| Idioma do template. | `en_US` | Não |

---

## 8. Servidor de Webhooks (WhatsApp / Meta API)

Para escutar eventos em tempo real do WhatsApp da Meta Cloud API:

1. **Início do Servidor:**
   ```bash
   python src/webhook_server.py
   ```
2. O servidor roda por padrão na porta `5000` (endpoint `/webhook`).
3. Para expor em homologação local, utilize um túnel HTTP (ex: `ngrok http 5000`).
4. **Token de Verificação GET:** O token pré-configurado é `rodolfo_hulk_tasmania` (definido em [webhook_server.py](../src/webhook_server.py#L7)).
5. **POST Handlers:** Processa payloads JSON enviados pela Meta com atualizações de entrega e status de leitura das mensagens.

---

## 9. Política de Versionamento e Roadmap (Semantic Versioning 2.0.0)

Este projeto adota estritamente o padrão **[Semantic Versioning (SemVer 2.0.0)](https://semver.org/lang/pt-BR/)** no formato `MAJOR.MINOR.PATCH`:

- **MAJOR (`X.0.0`) — Mudanças Estruturais / Breaking Changes**: Incompatibilidades no esquema do banco (`email_status_table`), refatorações centrais na arquitetura do daemon ou alteração nos contratos das interfaces de domínio.
- **MINOR (`1.X.0`) — Novas Funcionalidades (Retrocompatíveis)**: Novos provedores de mensagens, novas regras de transição/cupons, melhorias de infraestrutura ou utilitários CLI.
- **PATCH (`1.0.X`) — Bug Fixes e Ajustes Finos**: Correções de erros pontuais, ajustes de tratamento de logs ou refinamento em formatadores sem alteração de regras de negócio.

Os registros de versão são mantidos no arquivo [VERSION](../VERSION), detalhados no [CHANGELOG.md](../CHANGELOG.md) e marcados no Git através de **Annotated Tags** (ex: `git tag -a v6.2.0 -m "..."`).

> [!IMPORTANT]
> 🌊 **DIVISOR DE ÁGUAS — Transição da Fase 1 para a Fase 2**
> - **Fase 1 (v6.1.x e versões anteriores)**: Considerada a versão base oficial, 100% confiável (*reliable*) e totalmente operacional em produção para recuperação de carrinhos e acompanhamento de pedidos.
> - **Fase 2 (v6.2.0+)**: Representa a fase de aprimoramento e otimização contínua do sistema. A v6.2.0 estabelece o sistema de notificação reativa de exceções por e-mail (thread isolada), anexo de histórico de logs (~10MB/50k linhas) e integração com o Sentry SDK em nuvem. O planejamento evolutivo segue norteado por [07_future_implementations.md](../project_decisions/07_future_implementations.md).
