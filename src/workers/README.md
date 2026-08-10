# Workers (Regras de Negócio / Use Cases)

## Objetivo
É aqui que as regras de negócio da loja orquestram as dependências. Os *workers* são sub-programas projetados para realizar tarefas específicas (ex: Carrinho Abandonado).
Eles **nunca** instanciam clientes HTTP ou Bancos de Dados diretamente; eles recebem tudo via **Injeção de Dependência** em seus construtores e lidam exclusivamente com a lógica.

## Arquivos e Responsabilidades
- **`abandoned_cart.py`**: Implementa a classe `AbandonedCartProcessor`. Consulta os carrinhos via API, filtra pela janela de horas (ex: 2h após abandono), verifica o estado do disparo local para evitar duplicidade e orquestra o provedor de mensagem para contatar o cliente. Utiliza datas timezone-aware (`time_utils`) para cálculos precisos. A gravação final de estado na Fase 3 depende do sucesso do envio (False aborta a transição, garantindo que ela entre em modo de retentativa global no banco). A cada transição de `STC`, registra uma migalha de pão (`sentry_sdk.add_breadcrumb`) categorizada como `cart_state_machine` para auditoria e rastreio de causa-raiz.
- **`orders.py`**: Implementa a classe `OrderProcessor`. Lida com o ciclo de vida dos pedidos da loja, desde a confirmação de pagamento até lembretes para boletos e PIX e emissão de cupons de descontos para pedidos parados (STG) processando tudo concorrentemente com auxílio de injeção de estado no DB centralizado. Também utiliza datas timezone-aware (`time_utils`). Assim como em carrinhos, a transição só é gravada mediante sucesso reportado pelo provedor, evitando perda de estado em Timeouts de SMTP. **Validação estrita de rastreio:** A transição para `STG 3` (envio/rastreio) exige obrigatoriamente a presença do código de rastreio no payload da Yampi. Registra migalhas de pão (`sentry_sdk.add_breadcrumb`) categorizadas como `order_state_machine` a cada transição de `STG`.

## 🚨 Diretiva de Manutenção (Para IA e Desenvolvedores)
> [!IMPORTANT]
> **REGRA ESTRITA DE AUTO-DOCUMENTAÇÃO:**
> Sempre que for feito uma modificação, a documentação deve sofrer atualizações respectivas a essas mudanças.
> Se você criar uma nova rotina (ex: `payment_reminder.py` para boletos a vencer), **DEVE** atualizar este arquivo `README.md` explicando o fluxo lógico que foi implementado e quais as dependências injetadas que este novo worker utiliza.

## Dependências
- **`src/domain/`**: Workers interagem exclusivamente com as interfaces (Protocolos) definidas no Domínio.
- **Injeção de Instâncias (Em Tempo de Execução)**: O Worker espera receber instâncias concretas do cliente Yampi (`core/client.py`), o controle de estado (`ports/postgres_repo.py` ou `core/db.py`) e do provedor de mensageria (`ports/`).
- **Observabilidade**: `sentry-sdk` para rastreamento de breadcrumbs de negócios.

## Future Updates (Pontos a serem modificados e melhorados)
- Implementar processamento assíncrono nativo (`asyncio`) nos Workers para concorrência de alta escala além do ThreadPoolExecutor atual.
- Adicionar a capacidade de gerar relatórios consolidados sobre quantos disparos de carrinho abandonado reverteram em vendas na mesma janela de dia.
- Mudar para um sistema de Filas de Mensagens (ex: Celery, RabbitMQ ou AWS SQS) para enfileirar as ações dos Workers, em vez de depender de processamento *inline* longo caso o volume da loja cresça enormemente.
