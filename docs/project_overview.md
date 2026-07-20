# Comprehensive Project Guide: Message Integration

## 1. Visão Geral (Overview)
Este projeto é um sistema de integração de mensagens projetado para atuar no ecossistema de e-commerce (especialmente integrado à plataforma Yampi). O objetivo primário é fornecer funcionalidades de reengajamento com clientes e comunicação de atualizações vitais, tais como recuperação de carrinhos abandonados e atualizações de status de pedidos.

O sistema foi concebido utilizando metodologias ágeis sólidas:
- **Spec-driven development (SDD)**: Onde as interfaces e contratos são definidos antes das implementações.
- **Test-driven development (TDD)**: Onde testes orientam a lógica.

Este documento serve como o "Manual do Usuário" e o "Manual do Desenvolvedor" consolidado, fornecendo uma visão ampla, não-técnica e técnica detalhada do projeto de ponta a ponta.

---

## 2. Casos de Uso (Use Cases)

### 2.1 Recuperação de Carrinho Abandonado (Abandoned Cart)
- **Problema:** Clientes adicionam produtos ao carrinho, mas saem antes de finalizar a compra.
- **Ação do Sistema:** O sistema consulta a API da Yampi regularmente buscando por carrinhos recém-abandonados (baseando-se em uma janela de horas específica). 
- **Verificação:** Consulta um banco de dados local (SQLite/Postgres) para verificar se o cliente já foi notificado.
- **Execução:** Caso não tenha sido, despacha uma mensagem (via provedor de mensagem como WhatsApp ou Email) incentivando o retorno à loja.

### 2.2 Atualização de Pedidos (Orders Update)
- **Problema:** Clientes precisam estar informados do status de envio e processamento dos seus pedidos.
- **Ação do Sistema:** Atua reativamente (via webhooks) ou ativamente consultando status recentes.
- **Execução:** Envia atualizações via provedor de mensagem informando sobre pagamentos confirmados, mercadorias despachadas, etc.

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
- **Quem Executa (Regras de Negócio):** O diretório `src/workers/` possui os orquestradores (como `AbandonedCartProcessor`). Eles são o "cérebro" das tarefas individuais.
- **Onde Consulta (Fonte de Dados):**
  - **Externa:** API da Yampi consumida via `src/core/client.py`.
  - **Interna (Estado):** Banco de Dados, consultado via `src/core/db.py` (SQLite local) ou `src/ports/postgres_repo.py` para controle do que já foi enviado.
- **O Que Fornece (Saída/Output):** 
  - Comunicações enviadas via provedores de mensagens implementados em `src/ports/` (ex: WhatsApp Meta, SMTP Email, Mocks para testes locais).

---

## 5. Decisões de Projeto

- **Infraestrutura Desacoplada:** Ao usar os contratos de `src/domain/interfaces.py`, o projeto pode trocar de provedor de mensagem (Zenvia, Twilio, Meta) alterando apenas uma linha no orquestrador principal sem que o Worker perceba.
- **Tolerância a Falhas e Duplicidade:** O uso estrito do `StateRepositoryProtocol` (o DB local/Remoto) atua como um *Idempotency Key Store*, assegurando que gargalos de API ou retentativas não spammem o cliente final com o mesmo alerta duas vezes.
- **Auto-documentação (Spec-Driven):** Exigência de que regras e contratos guiem o desenvolvimento, sendo documentados e mantidos por IA em tempo real. Cada pasta possui seu próprio documento que reitera as limitações de modificação do módulo.

---

## 6. Logs e Depuração

### Fluxo de Logs
O sistema utiliza o módulo de logging nativo do Python configurado globalmente em [main.py](file:///home/luska/Documents/projects/message_integration/src/main.py).
- **Destinos da Saída:** Console (`sys.stdout`) e arquivo em disco (`logs/app.log`).
- **Nível de Logs:** `INFO`.
- **Rastreamento de Regras:** O worker de carrinhos calcula e loga a idade de abandono em horas (`Analisando carrinho [id]: abandonado há [X.XX] horas. Regra aplicada: [fase]`), facilitando o rastreamento das regras aplicadas para cada fase de recuperação.

### Depuração Interativa
Para rastrear a execução linha por linha e acompanhar a pilha de chamadas e objetos (incluindo chamadas de funções filhas) de forma visual:
*   **Depurador em IDE (VS Code):** Configurado no arquivo [.vscode/launch.json](file:///home/luska/Documents/projects/message_integration/.vscode/launch.json) para que o desenvolvedor possa colocar breakpoints no código e debugar de forma gráfica os comandos `abandoned-carts` e `orders` rodando localmente.

### Mapeamento no Docker
Para persistência local e facilidade de depuração no ambiente host, o [docker-compose.yml](file:///home/luska/Documents/projects/message_integration/docker-compose.yml) mapeia a pasta local `./logs` para `/app/logs` dentro do container da aplicação. Isso permite visualizar a execução em tempo real rodando comandos como `tail -f logs/app.log`.
