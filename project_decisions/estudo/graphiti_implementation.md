# Estudo de Implementação: Graphiti (Temporal Context Graphs) no Message Integration Yampi

## 1. O que é o Graphiti?
O [Graphiti](https://github.com/getzep/graphiti), criado pela Zep, é um framework open-source desenhado para a construção e consulta de **grafos de contexto temporais** (Temporal Context Graphs) para Agentes de IA. 

Diferente de bancos de dados relacionais tradicionais ou de abordagens estáticas de RAG (Retrieval-Augmented Generation), o Graphiti resolve o problema da "memória do agente" focando em:
- **Janelas de Validade (Temporal Fact Management):** O sistema entende quando um fato se tornou verdade e quando deixou de ser. (ex: "Cliente X tem um pedido pendente" -> "Cliente X pagou o pedido").
- **Ingestão Incremental e Proveniência (Episodes):** Toda informação no grafo é rastreável até o evento bruto (ex: o payload exato do webhook da Yampi). O grafo é atualizado em tempo real.
- **Busca Híbrida (Hybrid Retrieval):** Para recuperar o contexto de um cliente, o Graphiti combina busca semântica (vetores), palavras-chave (BM25) e travessia de grafo. Isso garante latência baixa e precisão sem depender de sumarizações lentas do LLM.

## 2. Qual o Encaixe (Fit) no Projeto Yampi?
Atualmente, o **Message Integration Yampi** automatiza recuperações (carrinho abandonado, boletos, pix) usando uma máquina de estados rígida, macros temporais e templates HTML fixos. Essa abordagem é eficiente e barata.

A adoção do Graphiti faz sentido **se a visão do produto for evoluir de uma "automação de e-mails rígida" para um "Agente Autônomo de Vendas e Suporte"** (especialmente útil se integrado com WhatsApp).

Com o Graphiti servindo como a "memória de longo prazo" do sistema, o agente de IA teria consciência temporal completa do cliente:
- O agente saberia que o cliente abandonou um tênis *hoje*, mas que comprou uma camiseta *mês passado*.
- O agente saberia que esse cliente tem o costume de gerar Boletos e não pagar, podendo adaptar a copy da mensagem para incentivar apenas compras no cartão de crédito ou Pix.

## 3. Como Implementar na Arquitetura Atual

Caso decidamos avançar, o Graphiti pode ser implementado no projeto com a seguinte arquitetura:

### A. Dependências de Infraestrutura (Stack)
- **Graph Database:** O Graphiti não roda no Postgres puro. Precisaremos adicionar um container do `Neo4j` (ou FalkorDB) ao nosso `docker-compose.yml`.
- **LLM Provider:** Uma conta da OpenAI (API Key). O Graphiti usa LLMs nos bastidores para extrair entidades e relações automaticamente durante a ingestão dos dados.
- **Python:** A biblioteca `graphiti` deve ser adicionada ao `requirements.txt`.

### B. Módulo de Ingestão (Webhooks -> Episodes)
Sempre que o `webhook_server.py` ou os workers processarem um evento da Yampi (ex: `abandoned_cart`), além do fluxo normal de salvamento no banco relacional, enviaríamos o payload para o Graphiti como um **Episode**.
- **Ontologia:** Definiríamos modelos Pydantic para as nossas entidades principais: `Customer` (Cliente), `Product` (Produto), `Order` (Pedido), `Cart` (Carrinho).
- Quando o Graphiti ingere o payload da Yampi, ele automaticamente criaria nós e relações no tempo, como: `Customer(Luska) --[ABANDONED at 14:00]--> Cart(Y) --[CONTAINS]--> Product(Tenis)`.

### C. Novo Worker: AI Conversation Agent
Poderíamos criar um novo worker, por exemplo `whatsapp_ai_worker.py`, que:
1. No momento de cobrar um carrinho abandonado, faz uma query no Graphiti pedindo todo o histórico e contexto ativo do cliente.
2. Injeta o subgrafo retornado no prompt de sistema de um LLM (ex: GPT-4o-mini).
3. O LLM gera uma mensagem de WhatsApp conversacional, empática e altamente personalizada, com base em todo o relacionamento temporal que a loja tem com o cliente.

## 4. Prós e Contras

| Vantagens (Prós) | Desvantagens (Contras) |
|------------------|------------------------|
| **Hiper-personalização Real:** As mensagens deixam de ser templates rígidos. A IA fala com o contexto completo do cliente. | **Custo Adicional Elevado:** Requer chamadas constantes de LLM apenas para a etapa de ingestão de webhooks no grafo, além da geração da resposta. |
| **Memória de Longo Prazo:** O sistema entende linhas do tempo de forma nativa. Fatos antigos são invalidados sozinhos quando novos webhooks chegam. | **Infraestrutura Mais Pesada:** Introduzir um banco de dados de grafos (Neo4j) aumenta a complexidade de manutenção e deploy da aplicação. |
| **Base para o Futuro:** Transforma a ferramenta de um "disparador" para um "agente inteligente", agregando extremo valor ao lojista. | **Overkill para E-mails Padrão:** Se o objetivo continuar sendo disparar e-mails de cobrança formatados (sem IA), o Graphiti não trará benefícios. |

## 5. Conclusão e Próximos Passos Recomendados

O Graphiti é uma ferramenta fantástica e de ponta (State of the Art) para **Memória de Agentes**. Sua implementação no *Message Integration Yampi* é recomendada **apenas se** o roadmap do produto incluir a criação de um atendente/vendedor de IA (provavelmente no WhatsApp).

Se o objetivo for manter a ferramenta leve, focada em automação baseada em regras (state-machines) e templates HTML de e-mail estáticos, a adição do Graphiti adicionaria complexidade e custos desnecessários.

**Plano de Ação caso seja aprovado (POC):**
1. Atualizar o `docker-compose.yml` para subir um banco `neo4j` local.
2. Instalar `graphiti` no `.venv`.
3. Criar um script `scripts/poc_graphiti.py` que puxa um JSON de mock da Yampi, cria um contexto temporal e faz uma pergunta usando o Graphiti para demonstrar a utilidade.
