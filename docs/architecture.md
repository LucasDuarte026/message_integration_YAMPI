# Arquitetura e Diretivas Spec-Driven

Este documento descreve a infraestrutura não-monolítica e orientada a especificações (Spec-Driven Development) deste projeto. 
Ele serve como guia principal e mapa mental para agentes de IA e desenvolvedores que trabalham nesta base de código.

## 🚨 Diretiva Crítica de Manutenção (Para Agentes de IA e Desenvolvedores)
> [!CAUTION]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> **SEMPRE QUE UM ARQUIVO FOR MODIFICADO, ADICIONADO OU REMOVIDO NESTE PROJETO:**
> Você **DEVE** atualizar imediatamente o arquivo `README.md` local do respectivo diretório onde a mudança ocorreu. Caso a mudança afete o fluxo geral, você deve atualizar este arquivo `architecture.md`. 
> A consistência e veracidade da documentação é um requisito estrito da nossa arquitetura Spec-Driven. Nunca escreva código sem documentar a mudança nos arquivos de documentação da pasta.

## Estrutura de Diretórios e Fluxo de Dados
O projeto adota uma variação de Clean Architecture / Hexagonal Architecture, dividida de forma que a Regra de Negócio não conheça os detalhes de Banco de Dados ou HTTP.

### Mapeamento Geral da Árvore de Arquivos
```bash
├── .gemini/                          # Diretrizes comportamentais de IA e regras de auto-documentação
│   ├── GEMINI.md                     # Código de conduta do assistente, Git em modo leitura, SemVer
│   └── auto_documentation_rules.md   # Regras de manutenção síncrona dos README.md locais
├── docs/                             # Documentação geral do sistema
│   ├── architecture.md               # Detalhes da arquitetura de especificação e camadas
│   ├── diagramas/                    # Diagramas Mermaid da máquina de estados (STG/STC)
│   │   ├── README.md                 # Índice e guia visual dos diagramas
│   │   ├── stateDiagramAbandonedCarts.md # Diagrama Mermaid do fluxo STC (Carrinhos)
│   │   └── stateDiagramOrders.md     # Diagrama Mermaid do fluxo STG (Pedidos)
│   ├── project_dependency_tree.md    # Árvore visual e conceitual de dependências
│   ├── project_overview.md           # Guia funcional completo e decisões de design
│   ├── email_state_machine.md        # Especificação técnica da Máquina de Estados (STG/STC)
│   └── docker_cheatsheet.md          # Guia de rotinas e comandos Docker
├── emails/                           # Diretório de auditoria contendo HTMLs de envios passados
├── estudos/                          # Documentações e relatórios de estudos de mercado/CPaaS
├── src/                              # Código-fonte principal
│   ├── core/                         # Infraestrutura interna básica do sistema
│   │   ├── client.py                 # Cliente de integração com a API da Yampi
│   │   ├── config.py                 # Dataclasses de configuração e ambiente
│   │   ├── db.py                     # Controle de estado SQLite local
│   │   ├── logging_config.py         # Configuração de Logs e Interceptação Global de Erros
│   │   └── macros.py                 # Constantes e paramêtros temporais do sistema
│   ├── domain/                       # Camada de contratos estritos e specs
│   │   └── interfaces.py             # Protocols e Classes Abstratas do sistema
│   ├── ports/                        # Adaptadores de APIs de terceiros (Meta, SMTP, Mock)
│   │   ├── message_provider.py       # Mock Provider de Dry-run
│   │   ├── smtp_email_provider.py    # Adaptador de envio de E-mail via SMTP
│   │   └── whatsapp_meta_provider.py # Adaptador de envio de WhatsApp via Meta Cloud API
│   ├── services/                     # Lógica de serviços injetáveis (ex: email_builders)
│   ├── templates/                    # MVC de E-mails (config, mjml, assets, html_compiled e builder)
│   ├── workers/                      # Casos de uso e regras de negócio orquestradas
│   │   └── abandoned_cart.py         # Threaded-worker de recuperação de carrinhos
│   ├── main.py                       # CLI principal do projeto (Orquestrador)
│   └── webhook_server.py             # Servidor HTTP para Webhooks da Meta API
├── tests/                            # Testes unitários do sistema
│   └── test_abandoned_cart.py        # Casos de teste do fluxo de carrinhos
├── scripts/                          # Pasta de scripts utilitários de execução e consulta ao BD
├── studies/                          # Amostras de dados de API, payloads e referências
├── .env                              # Credenciais e parâmetros de ambiente (NUNCA versionar)
├── .env.example                      # Modelo de exemplo para o .env
├── Dockerfile                        # Receita da imagem do container da aplicação
├── docker-compose.yml                # Orquestrador local da aplicação e do Postgres DB
├── README.md                         # Visão geral e guia rápido do repositório
├── run_local.sh                      # Wrapper de atalho raiz para scripts/run_local.sh
├── requirements.txt                  # Dependências do Python
└── state.db                          # Banco de dados SQLite persistente (gerado na execução)
```

### 1. [`src/domain/`](../src/domain/README.md) (As Especificações)
O coração da aplicação. Não possui implementações, apenas contratos (`Protocols`, `Interfaces`, `ABC`). Tudo no sistema depende do domínio, mas o domínio não depende de nada. Se você vai criar uma funcionalidade nova, **comece especificando-a aqui**.

### 2. [`src/core/`](../src/core/README.md) (Infraestrutura Base e Clientes Internos)
Fornece os blocos de construção internos da nossa infraestrutura:
- Conexão e tratamento bruto com a API Yampi (`client.py`)
- Gerenciamento de credenciais via variáveis de ambiente (`config.py`)
- Repositório de estado / persistência local e relacional e parâmetros temporais (`db.py` e `macros.py`)
- Configuração do Logger central e Interceptação Global de Exceções (`logging_config.py`)

### 3. [`src/ports/`](../src/ports/README.md) (Adaptadores Externos)
Onde as implementações de terceiros (que não são o nosso sistema core) vivem. Eles implementam os contratos do `domain`.
- Exemplo: Provedores de envio de mensagens via WhatsApp/Email (SMTP, Mocks).
- Exemplo: Implementação do banco de dados relacional (PostgreSQL via `postgres_repo.py`).

### 4. [`src/workers/`](../src/workers/README.md) (Regras de Negócio e Use Cases)
Os sub-programas que executam as atividades (ex: Recuperação de Carrinho Abandonado e Atualização de Pedidos). Os workers são isolados, não instanciam conexões e devem receber todas as dependências (Core e Ports) injetadas no construtor pelo Orquestrador.
> **NOTA:** A lógica de estado (STG e STC) processada pelos workers é estritamente regida pela **[Lógica e Máquina de Estados de E-mails](./email_state_machine.md)**. Qualquer mudança na regra de negócio deve primeiro ser modelada naquele documento.

### 5. `src/main.py` (Orquestrador / Ponto de Entrada)
É quem junta tudo. Ele importa as configurações, cria a instância do banco de dados, a instância da API, e as passa como dependência para o Worker desejado. É desenhado para ser executado via CLI (ex: `crontab`).

### 6. `src/webhook_server.py` (Servidor de Webhooks)
Servidor Flask independente que escuta na porta 5000 para receber validações de token (GET) e payloads de mensagens/status em tempo real (POST) vindos da Meta API.

---

## 💻 Especificação de Hardware e Dimensionamento (Benchmarking)

O sistema passou por baterias empíricas de testes de estresse e longa exposição (1h 35min contínuos), documentadas em [`project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md`](../project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md).

### Requisitos Empíricos do Sistema
* **Memória RAM Total do Stack:** ~177 MiB de pico máximo (ausência completa de *memory leaks* após 95 minutos de execução contínua).
* **Processamento CPU Total do Stack:** ~1.72 vCPUs de pico máximo sob alta carga paralela.

### Limites Definitivos no `docker-compose.yml`
* **`app` (Aplicação):**
  * `limits`: CPU: `1.50 vCPU` | RAM: `512 MB`
  * `reservations`: CPU: `0.50 vCPU` | RAM: `256 MB`
* **`db` (PostgreSQL):**
  * `limits`: CPU: `0.80 vCPU` | RAM: `512 MB`
  * `reservations`: CPU: `0.20 vCPU` | RAM: `128 MB`

### Justificativa de Escolha de Infraestrutura (Sizing)
* **Por que X vCPUs (2.30 vCPUs total estipulado no Docker Compose)?** Garante que o pico de 1.72 vCPUs da aplicação e banco de dados seja processado sem nenhum estrangulamento de CPU (*throttling*).
* **Por que Y MB RAM (512 MB por contêiner / 1 GB total)?** Oferece uma margem de segurança de **3x sobre o consumo de pico real (~177 MB)**, prevenindo completamente qualquer risco de *Out of Memory Kill (OOMKill)*.
* **Provedor de Nuvem Recomendado:**
  * **Hostinger KVM 2** (2 vCPUs / 8 GB RAM) — R$ 42,99/mês (ou KVM 1 para MVP de custo reduzido por R$ 29,99/mês).
  * **AWS EC2 `t3.medium`** (2 vCPUs / 4 GB RAM) ou **AWS ECS Fargate (2 vCPU / 4 GB RAM)**.

