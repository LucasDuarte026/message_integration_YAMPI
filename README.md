# Message Integration 🚀

Este projeto é uma ferramenta de integração de mensageria para e-commerce baseada em **Arquitetura Hexagonal (Ports & Adapters)** e **Spec-Driven Development**. 
O objetivo principal é a recuperação de carrinhos abandonados da plataforma **Yampi**, notificando os clientes de forma automatizada por e-mail ou WhatsApp.

---

## 📋 Sumário

1. [Visão Geral](#visão-geral)
2. [Arquitetura do Projeto](#arquitetura-do-projeto)
3. [Documentação do Projeto e Diretrizes de IA](#documentação-do-projeto-e-diretrizes-de-ia)
4. [Pré-requisitos e Instalação](#pré-requisitos-e-instalação)
5. [Configuração (Variáveis de Ambiente)](#configuração-variáveis-de-ambiente)
6. [Como Utilizar](#como-utilizar)
   - [Execução do Worker (Recuperação de Carrinho)](#execução-do-worker-recuperação-de-carrinho)
   - [Servidor de Webhook (WhatsApp/Meta)](#servidor-de-webhook-whatsappmeta)
7. [Executando os Testes](#executando-os-testes)
8. [Logs e Depuração (Auditoria)](#logs-e-depuração-auditoria)
9. [Estrutura de Diretórios](#estrutura-de-diretórios)
10. [Versionamento e Roadmap](#versionamento-e-roadmap-semantic-versioning)

---

## Visão Geral

O sistema funciona buscando ciclicamente os carrinhos abandonados diretamente da API da Yampi. Ele filtra os registros com base em regras de tempo (idade de abandono do carrinho) e verifica no banco de dados SQLite local (`state.db`) se o cliente já recebeu a notificação correspondente. Isso garante que cada cliente receba exatamente um e-mail de lembrete por carrinho abandonado, evitando disparos duplicados ou spam.

### Principais Funcionalidades:
- **Busca Incremental & Paginação**: Integração robusta com a API de checkout da Yampi, tratando paginação automática, limites de requisição (*Rate Limits* - HTTP 429) e exclusão de cache.
- **Processamento Assíncrono/Concorrente**: Dispara os e-mails e gera os relatórios em paralelo via `ThreadPoolExecutor`, agilizando a execução.
- **Persistência de Estado**: Banco SQLite local que armazena a relação de carrinhos que já receberam notificações.
- **Multi-Provedores (Ports)**:
  - `DryRunMessageProvider`: Para simulação e testes locais sem custos de API.
  - `SMTPEmailProvider`: Para envio real de e-mails em produção utilizando credenciais SMTP.
  - `WhatsAppMetaProvider`: Para integração com a Cloud API oficial da Meta (WhatsApp Business).
- **Servidor Webhook**: Um micro-serviço em Flask preparado para receber as validações de Token GET e atualizações de entrega/status de mensagens via POST do WhatsApp da Meta.

---

## Arquitetura do Projeto

O projeto segue os princípios da Clean/Hexagonal Architecture:
- **Domínio (`src/domain/`)**: Contém os contratos e interfaces ([interfaces.py](./src/domain/interfaces.py)). Nada fora desta pasta depende de implementações de rede, banco de dados ou APIs de terceiros.
- **Core (`src/core/`)**: Infraestrutura base interna do sistema, como o cliente HTTP para a Yampi ([client.py](./src/core/client.py)), o repositório de estado SQLite ([db.py](./src/core/db.py)) e as configurações ([config.py](./src/core/config.py)).
- **Adaptadores/Ports (`src/ports/`)**: Conexões com serviços de terceiros que implementam as interfaces do domínio ([smtp_email_provider.py](./src/ports/smtp_email_provider.py), [whatsapp_meta_provider.py](./src/ports/whatsapp_meta_provider.py) e [message_provider.py](./src/ports/message_provider.py)).
- **Workers (`src/workers/`)**: Regras de negócio e lógica de orquestração de use cases, como o processador de carrinhos abandonados ([abandoned_cart.py](./src/workers/abandoned_cart.py)). Eles recebem todas as dependências por Injeção de Dependência no construtor.

---

## Documentação do Projeto e Diretrizes de IA

O projeto adota uma abordagem de **Spec-Driven Development (SDD)**, onde a documentação é tratada como código de primeira classe. A base de documentação do repositório está estruturada principalmente em duas pastas: **`.gemini/`** e **`docs/`**.

### 1. Pasta `.gemini/` (Diretrizes de Agentes e Auto-documentação)
Esta pasta contém as regras comportamentais e diretivas estritas de desenvolvimento para assistentes de IA (como Antigravity, Gemini e Claude) e desenvolvedores:
- **[`.gemini/GEMINI.md`](./.gemini/GEMINI.md)**: Define o código de conduta do assistente de IA. Estabelece o idioma oficial em Português (Brasil), a **Regra de Ouro do Git** (a IA pode apenas executar comandos consultivos de leitura, nunca mutações como `commit` ou `push`), padrões de versão (SemVer 2.0.0), alterações cirúrgicas e o uso de diagramas Mermaid.
- **[`.gemini/auto_documentation_rules.md`](./.gemini/auto_documentation_rules.md)**: Define as regras de auto-documentação contínua. Exige que qualquer alteração de código seja acompanhada da atualização síncrona do arquivo `README.md` do diretório ("braço") correspondente em `src/`.

### 2. Pasta `docs/` (Arquitetura, Casos de Uso e Operação)
Esta pasta armazena a documentação técnica e funcional de suporte:
- **[`docs/architecture.md`](./docs/architecture.md)**: Mapa mental e índice navegável dos braços do sistema (`src/domain/`, `src/core/`, `src/ports/`, `src/workers/`), detalhando as camadas da Clean/Hexagonal Architecture.
- **[`docs/project_dependency_tree.md`](./docs/project_dependency_tree.md)**: Diagrama visual e hierárquico da árvore de dependências da arquitetura.
- **[`docs/project_overview.md`](./docs/project_overview.md)**: Guia funcional cobrindo casos de uso (recuperação de carrinho, atualização de pedidos), fluxo de execução sequencial e decisões arquiteturais.
- **[`docs/email_state_machine.md`](./docs/email_state_machine.md)**: Especificação formal da máquina de estados dupla (STG/STC), schema do banco e concorrência.
- **[`docs/future_implementations.md`](./docs/future_implementations.md)**: Roadmap de refatorações futuras e débitos técnicos.
- **[`docs/docker_cheatsheet.md`](./docs/docker_cheatsheet.md)**: Guia prático de comandos e rotinas para gerenciamento de containers Docker.

### 🚨 Diretivas Obrigatórias de Auto-Documentação e Manutenção
> [!IMPORTANT]
> **REGRAS PARA INÍCIO DE SESSÃO / NOVOS CHATS DA IA E DESENVOLVEDORES:**
> 1. **Consulta Obrigatória**: Sempre que um novo chat ou sessão for iniciado com assistentes de IA, o assistente **DEVE obrigatoriamente carregar e consultar o conteúdo das pastas `.gemini/` e `docs/`**, bem como o `README.md` local do módulo em que atuará, antes de planejar, propor ou executar qualquer alteração no código-fonte.
> 2. **Sincronia de Documentação (Regra Estrita)**: Sempre que for feita uma modificação no sistema (criação, alteração ou exclusão de arquivos), a documentação correspondente (este `README.md`, os da pasta `docs/` e os arquivos README marginais nas subpastas) deve sofrer atualizações respectivas a essas mudanças imediatamente, mantendo a estrutura em árvore (`Geral -> docs -> Específico da subpasta`).

---

## Pré-requisitos e Instalação

### Opção A: Execução Local (Python Nativo)
- **Python 3.8+**
- Ambiente Virtual (reconhecido localmente no projeto como `.venv`)

1. Certifique-se de que o seu ambiente virtual está ativo:
   ```bash
   source .venv/bin/activate
   ```
2. Instale as dependências listadas no arquivo [requirements.txt](./requirements.txt):
   ```bash
   pip install -r requirements.txt
   ```

### Opção B: Execução em Containers (Docker & Docker Compose) - Recomendado 🐳
- **Docker** e **Docker Compose** instalados no sistema.
1. Crie o arquivo `.env` na raiz do projeto com base nas suas credenciais:
   ```bash
   cp .env.example .env
   # Preencha o .env com seus tokens de acesso Yampi e chaves de envio
   ```

---

## Configuração (Variáveis de Ambiente)

O arquivo [config.py](./src/core/config.py) carrega as configurações da aplicação com base nas variáveis de ambiente. Defina-as no terminal antes da execução ou crie um arquivo `.env` (se houver suporte local):

| Variável | Descrição | Padrão | Obrigatória? |
| :--- | :--- | :--- | :--- |
| `YAMPI_USER_TOKEN` | Token do usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_USER_SECRET_KEY` | Chave secreta de usuário do painel da Yampi. | - | **Sim** |
| `YAMPI_ALIAS` | Alias da sua loja Yampi (opcional; detectado automaticamente se omitido). | - | Não |
| `SQLITE_DB_PATH` | Caminho do arquivo SQLite para persistir estados. | `state.db` | Não |
| `TEST_EMAIL_RECIPIENT` | E-mail de destino para envio em modo de teste/homologação. | `wpplucas026@gmail.com` | Não |
| `MAX_CART_AGE_HOURS` | Limite de tempo em horas (cutoff) para desconsiderar carrinhos muito antigos. | `48` | Não |
| `MAX_WORKERS` | Quantidade máxima de threads paralelas para processamento. | `10` | Não |
| **SMTP Configs (Produção)** | | | |
| `SMTP_USER` | Usuário de autenticação do servidor SMTP. | - | **Sim (Modo Produção)** |
| `SMTP_PASSWORD` | Senha ou Token de App do e-mail SMTP. | - | **Sim (Modo Produção)** |
| `SMTP_HOST` | Host do servidor de e-mail. | `smtp.gmail.com` | Não |
| `SMTP_PORT` | Porta do servidor SMTP (usar `465` para SSL ou `587` para TLS). | `587` | Não |
| `SMTP_FROM` | E-mail remetente que aparecerá no cabeçalho do destinatário. | `SMTP_USER` | Não |
| **Meta WhatsApp Configs** | | | |
| `META_WA_TOKEN` | Token temporário ou permanente da Meta Cloud API. | - | Não |
| `META_PHONE_NUMBER_ID` | Identificador de número de telefone gerado na Meta Cloud API. | - | Não |
| `META_WA_TEMPLATE_NAME`| Nome do template homologado no painel da Meta. | `hello_world` | Não |
| `META_WA_TEMPLATE_LANG`| Idioma do template. | `en_US` | Não |

---

## Como Utilizar

### Opção A: Usando Docker (Recomendado) 🐳

1. **Subir os Serviços (Banco PostgreSQL e Container da Aplicação em modo ocioso):**
   ```bash
   docker compose up -d
   ```
   *Isso subirá o banco PostgreSQL na rede interna e manterá a aplicação pronta e aguardando comandos manuais de execução (o servidor de webhook está desativado por padrão).*

2. **Executar as Rotinas do Worker (CLI) dentro do Container Ativo:**
   Como o container já está rodando em segundo plano de forma ociosa, você pode rodar os comandos de forma instantânea usando `exec`:
   ```bash
   # Rodar worker de Orders (Pedidos)
   docker compose exec app python src/main.py orders
   
   # Rodar worker de Abandoned Carts (Carrinho Abandonado)
   docker compose exec app python src/main.py abandoned-carts
   
   # Rodar com a flag de Produção
   docker compose exec app python src/main.py abandoned-carts --production
   ```
   *(Caso prefira subir containers temporários e removê-los após o término, você pode utilizar `docker compose run --rm app python src/main.py [comando]` em vez de `exec`)*

3. **Verificar os logs dos containers:**
   ```bash
   docker compose logs -f
   ```

---

### Opção B: Execução Manual (Localmente)

### Execução do Worker (Recuperação de Carrinho)

O orquestrador principal do projeto é o [main.py](./src/main.py). Você pode executá-lo através da CLI passando comandos específicos.

#### 1. Modo Dry-Run (Simulado)
Por padrão, a execução utiliza mocks de e-mail e de WhatsApp para exibir os envios diretamente no terminal sem gerar custos de API ou enviar e-mails reais:
```bash
python src/main.py abandoned-carts
```
*Durante o Dry-Run, o corpo HTML dos e-mails gerados é salvo localmente no arquivo `tests/temp_email_output.html` para validação visual.*

#### 2. Modo Produção (Envio de E-mail Real via SMTP)
Para disparar e-mails reais para os clientes utilizando as credenciais SMTP definidas, passe a flag `--production`:
```bash
python src/main.py abandoned-carts --production
```
> [!IMPORTANT]
> Lembre-se de preencher `SMTP_USER` e `SMTP_PASSWORD` no seu ambiente antes de rodar com a flag `--production`.

---

### Servidor de Webhook (WhatsApp/Meta)

Para rodar o servidor Flask que escuta os eventos em tempo real do WhatsApp da Meta:

1. Inicie o servidor:
   ```bash
   python src/webhook_server.py
   ```
2. O servidor ficará ativo na porta `5000` (ex: `http://localhost:5000/webhook`).
3. Use uma ferramenta de túnel (como o *ngrok*) para expor a porta local para a internet:
   ```bash
   ngrok http 5000
   ```
4. Configure a URL gerada pelo ngrok finalizada em `/webhook` nas configurações do Webhook da Meta Business Cloud API.
5. Utilize o Token de Verificação padrão: `rodolfo_hulk_tasmania` (configurado em [webhook_server.py](./src/webhook_server.py#L7)).

---

## Executando os Testes

Os testes unitários cobrem a validação de regras de negócios de elegibilidade (cutoff de 2 horas e limite de 48 horas), tratamento de carrinhos elegíveis, ignorados, repetidos e tratamento de mocks de rede e persistência.

Para executar os testes contidos na pasta [tests](./tests), use o interpretador do ambiente virtual:

```bash
./.venv/bin/python -m unittest discover -s tests
```

---

## Logs e Depuração (Auditoria)

### Logs de Execução (Console e Arquivo)
A aplicação possui um sistema de logging configurado em [main.py](./src/main.py). O tempo de abandono dos carrinhos em horas é registrado durante a análise.
*   **Caminho local:** `logs/app.log` (mapeado via volume no Docker Compose).
*   **Visualização em tempo real:** `tail -f logs/app.log`

### Depuração Interativa (VS Code)
Para acompanhar a execução do código passo a passo (incluindo chamadas internas/filhas) de maneira visual:
*   Use as configurações do [launch.json](./.vscode/launch.json) integradas no VS Code. Basta acessar a aba "Run and Debug", escolher o perfil correspondente ao worker e pressionar **F5** após definir seus breakpoints.

### Auditoria de Templates de E-mail
A cada execução do worker de carrinhos abandonados, os e-mails HTML gerados dinamicamente para cada carrinho são salvos localmente:
*   **Caminho:** `emails/cart_{id_do_carrinho}/email.html`
*   Isso facilita a auditoria manual dos dados e do layout gerado para o cliente.

---

## Estrutura de Diretórios

Abaixo está o mapeamento dos principais componentes do projeto:

```bash
├── .gemini/                          # Diretrizes comportamentais de IA e regras de auto-documentação
│   ├── GEMINI.md                     # Código de conduta do assistente, Git em modo leitura, SemVer
│   └── auto_documentation_rules.md   # Regras de manutenção síncrona dos README.md locais
├── docs/                             # Documentação geral do sistema
│   ├── architecture.md               # Detalhes da arquitetura de especificação e camadas
│   ├── project_dependency_tree.md    # Árvore visual e conceitual de dependências
│   ├── project_overview.md           # Guia funcional completo e decisões de design
│   ├── email_state_machine.md        # Especificação técnica da Máquina de Estados (STG/STC)
│   ├── future_implementations.md     # Débitos técnicos e roadmap de novas features
│   └── docker_cheatsheet.md          # Guia de rotinas e comandos Docker
├── emails/                           # Diretório de auditoria contendo HTMLs de envios passados
├── estudos/                          # Documentações e relatórios de estudos de mercado/CPaaS
├── src/                              # Código-fonte principal
│   ├── core/                         # Infraestrutura interna básica do sistema
│   │   ├── client.py                 # Cliente de integração com a API da Yampi
│   │   ├── config.py                 # Dataclasses de configuração e ambiente
│   │   └── db.py                     # Controle de estado SQLite local
│   ├── domain/                       # Camada de contratos estritos e specs
│   │   └── interfaces.py             # Protocols e Classes Abstratas do sistema
│   ├── ports/                        # Adaptadores de APIs de terceiros (Meta, SMTP, Mock)
│   │   ├── message_provider.py       # Mock Provider de Dry-run
│   │   ├── smtp_email_provider.py    # Adaptador de envio de E-mail via SMTP
│   │   └── whatsapp_meta_provider.py # Adaptador de envio de WhatsApp via Meta Cloud API
│   ├── workers/                      # Casos de uso e regras de negócio orquestradas
│   │   └── abandoned_cart.py         # Threaded-worker de recuperação de carrinhos
│   ├── main.py                       # CLI principal do projeto (Orquestrador)
│   └── webhook_server.py             # Servidor HTTP para Webhooks da Meta API
├── tests/                            # Testes unitários do sistema
│   └── test_abandoned_cart.py        # Casos de teste do fluxo de carrinhos
├── requirements.txt                  # Dependências do Python
└── state.db                          # Banco de dados SQLite persistente (gerado na execução)
```

---

## Versionamento e Roadmap (Semantic Versioning)

Este projeto adota estritamente o padrão **[Semantic Versioning (SemVer 2.0.0)](https://semver.org/lang/pt-BR/)** no formato `MAJOR.MINOR.PATCH`:

- **MAJOR (`X.0.0`)** — **Big Changes / Breaking Changes**: Mudanças estruturais grandes ou incompatíveis na arquitetura, modelos de banco de dados ou contratos de APIs.
  - **`v1.0.0` (Atual / Baseline)**: Sistema legado dockerizado com tabelas separadas (`cart_states`, `order_states`) e fluxo inicial de e-mails/WhatsApp.
  - **`v2.0.0` (Próxima / Planejada)**: Refatoração completa para máquina de estados dupla (STG/STC), tabela unificada `email_status_table` com locking, e consumo de arquivos JSON em lotes de 100 (especificada em `04_refactor_logic_emails.md`).
- **MINOR (`1.X.0`)** — **Novas Funcionalidades (Non-breaking)**: Adição de novos provedores (ex: novos canais de mensagem, novas regras de cupons) de forma retrocompatível.
- **PATCH (`1.0.X`)** — **Bug Fixes / Ajustes Pequenos**: Correções de bugs, pequenas melhorias de performance ou ajustes de formatação sem alterar regras de negócio.

Os registros de cada versão e histórico de alterações estão centralizados no arquivo [`CHANGELOG.md`](./CHANGELOG.md) e controlados via Git Tags (ex: `git tag v1.0.0`).

