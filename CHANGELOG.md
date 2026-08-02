# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [6.2.1] - 2026-08-01 (Especificação Definitiva de Hardware e Limites Docker - STABLE)

### 📌 Status da Release: **ESTÁVEL (STABLE)**

### Adicionado / Modificado
- **Limites de Recursos Definitivos (`docker-compose.yml`)**:
  - Definidos limites definitivos e reservas de recursos para garantir estabilidade operacional e previsibilidade de custos em nuvem (Hostinger KVM / AWS).
  - **`app` (Aplicação)**: `limits` = 1.50 vCPU / 512 MB RAM | `reservations` = 0.50 vCPU / 256 MB RAM.
  - **`db` (PostgreSQL)**: `limits` = 0.80 vCPU / 512 MB RAM | `reservations` = 0.20 vCPU / 128 MB RAM.
  - Comentários detalhados adicionados no `docker-compose.yml` justificando cada limite com base nos testes empíricos de carga.
- **Módulo de Estudos de Capacidade (`project_decisions/estudos/hardware_specs/`)**:
  - Criado o relatório consolidado [`ESTUDO_CAPACIDADE_HARDWARE.md`](./project_decisions/estudos/hardware_specs/ESTUDO_CAPACIDADE_HARDWARE.md) registrando a bateria de 4 testes de estresse, simulação KVM 1 e o teste de longa exposição de 1 hora e 35 minutos (95 min).
  - Provado empiricamente a **ausência total de vazamentos de memória (*memory leaks*)** (variação de RAM total do stack de apenas 24 MB ao longo de 95 min).
  - Desenvolvido o script Python de automação [`medir_recursos.py`](./project_decisions/estudos/hardware_specs/medir_recursos.py) para medição contínua e salvamento automático de logs em `logs/`.
- **Documentação de Arquitetura (`docs/architecture.md` e `docs/README.md`)**:
  - Adicionada a seção **"Especificação de Hardware e Dimensionamento (Benchmarking)"** com a justificativa de dimensionamento (Sizing X vCPUs / Y MB RAM) para embasar decisões futuras de nuvem.
  - Links relativos portáveis padronizados conforme as diretivas do `.gemini/auto_documentation_rules.md`.

> [!NOTE]
> ⚠️ **AVISO DE PRODUÇÃO (NÃO OFICIAL PARA ENVIO REAL)**:
> Esta versão é **estável** em termos de arquitetura, estabilidade e gerenciamento de recursos. No entanto, o envio oficial de e-mails para clientes reais via servidor Hostinger SMTP **ainda não está ativado** (`MACRO_ENABLE_REAL_EMAIL_DISPATCH = False` e `MACRO_FORCE_TEST_EMAIL_RECIPIENT = True` em `src/core/macros.py`).

---

## [6.2.0] - 2026-08-01 (Notificação Reativa de Erros e Integração Sentry)

### Adicionado / Modificado
- **Observabilidade e Alertas de Erros (`src/core/logging_config.py`)**:
  - Implementado interceptador de exceções não tratadas (`sys.excepthook` e `threading.excepthook`) acionando thread em background para envio automático de e-mail com relatório de falha e anexo contendo as últimas 50.000 linhas (~10MB) do log `app.log`.
  - Adicionadas configurações dedicadas para servidor SMTP de traceback (`TRACEBACK_SMTP_*` e `TRACEBACK_EMAIL_RECIPIENT`) permitindo isolamento total do servidor SMTP de clientes.
- **Integração Sentry SDK**:
  - Atualizado `sentry-sdk` para `2.66.1` no `requirements.txt` com tratamento de resiliência `ImportError`.
  - Documentação e padronização completa de variáveis no `.env.example`.
- **Organização e Roadmap (`project_decisions/07_future_implementations.md`)**:
  - Oficializada a estabilização da Fase 1 (v1.0.0 / v6.1.x) e movido o roadmap de implementações futuras para `project_decisions/07_future_implementations.md`.

> [!IMPORTANT]
> 🌊 **DIVISOR DE ÁGUAS — Transição para a Fase 2 (Aprimoramento do Sistema)**
> - **Fase 1 (v6.1.x e anteriores)**: Declarada oficial, 100% confiável (*reliable*) e totalmente operacional para recuperação de carrinhos e pedidos Yampi via SMTP/WhatsApp.
> - **Fase 2 (v6.2.0+)**: Início do ciclo de aprimoramentos técnicos, observabilidade avançada, notificações reativas de falha e evolução do produto descritos em `project_decisions/07_future_implementations.md`.

---

## [6.1.2] - 2026-08-01 (Isolamento de Volumes Docker e Mapeamento de Logs)

### Adicionado / Modificado
- **Docker e Infraestrutura (`docker-compose.yml`)**:
  - Ajustado o mapeamento de volumes no `docker-compose.yml` para direcionar a pasta do host `./containers/logs` e `./containers/emails` para `/app/local_data/logs` e `/app/local_data/emails` dentro do container.
  - Garante o isolamento completo entre arquivos de teste locais (`./local_data/`) e arquivos gerados em container (`./containers/`).
- **Configuração de Macros (`src/core/macros.py`)**:
  - Atualizadas macros globais de disparo e avisos de segurança no modo de teste.

## [6.1.1] - 2026-08-01 (Correção do Carregamento Local de Imagens e Mocks de E-mail)

### Corrigido
- **Mocks de E-mail e Builder (`builder.py`)**:
  - Corrigido cálculo de caminho base no `builder.py` para utilizar `current_dir / "assets" / "images"`, eliminando a busca em caminho duplicado `/src/src/...` e resolvendo a injeção do placeholder `Folder Not Found`.
  - Removida restrição de prefixo hardcoded na busca de imagens de body nos e-mails de cupom (15% e 20% OFF), garantindo a detecção automática de imagens com novos nomes (`15_desconto.png.png` e `20_desconto.png.png`).
  - Regerados todos os HTMLs de mock na pasta `src/templates/emails/mocks/` com caminhos de imagem `file:///` locais funcionais.

## [6.1.0] - 2026-07-31 (Correção de CID no Docker)

### Corrigido
- **E-mails sem Imagem**: Corrigido um bug silencioso de _path traversal_ no `SMTPEmailProvider` ao ser rodado dentro do Docker. O algoritmo voltava 3 níveis (resultando em `/` no Linux) em vez de 2 níveis (`/app`), o que impedia a anexação de imagens locais via CID e resultava em e-mails com URLs originais relativas sendo reescritas (quebradas) pelo proxy do Gmail.

## [6.0.0] - 2026-07-31 (Auditoria de Segurança Reliable)

### Adicionado / Modificado
- **AppSec (Segurança da Aplicação)**:
  - Implementado teto máximo (*cap*) de 60 segundos no backoff de Rate Limit (`client.py`).
  - Adicionado timeout explícito `timeout=(5, 15)` nas chamadas HTTP (`requests`).
  - Passado flag `verify=True` forçando verificação estrita de TLS contra ataques MitM.
- **DataSec (Segurança de Dados e PII)**:
  - Adicionado `sentry-sdk` (`v2.0.0`) para atuar como interceptador de erros globais (Data Scrubbing), prevenindo o vazamento de tokens e payloads no traceback salvo em disco (`app.log`).
  - Ofuscação proativa do e-mail de destino no `SMTPEmailProvider` para complacência com LGPD.
