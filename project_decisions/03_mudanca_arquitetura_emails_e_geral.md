# Decisão 03: Plano de Refatoração e Remodelação Geral da Arquitetura

**Data de Criação:** 2026-07-20  
**Última Atualização:** 2026-07-20  
**Versão:** 0.1.0  
**Status:** Em Desenvolvimento / Rascunho  
**Escopo:** Refatoração ponta a ponta da estrutura do projeto, modelo de dados, logs e padronização.

---

## Visão Geral

Este documento servirá como base para uma refatoração completa do projeto. O objetivo é repensar a finalidade dos processos do sistema, remodelar a estrutura de diretórios e a lógica de negócios que sustentam as novas funcionalidades de mensageria.

---

## 1. Diretrizes de Padronização e Formato do Plano

* **Fase 1 (Padronização da Documentação)**:
  Reescrita e padronização de todos os arquivos de decisões (`.md`) da pasta `project_decisions/`, garantindo consistência visual, títulos descritivos, badges de status e marcação histórica de datas de atualização.
* **Fase 2 (Plano de Remodelação)**:
  Definição do plano de ação para refatoração e expansão de recursos, incluindo rastreabilidade de erros, sistema de logs e isolamento de portas/adaptadores.

---

## 2. Pilares da Nova Arquitetura

1. **Rastreabilidade e Tratamento de Exceções**:
   Substituição de capturas genéricas por exceções de domínio tipadas e sistema de logs centralizado com níveis apropriados (`INFO`, `WARNING`, `ERROR`).
2. **Escalabilidade e Inversão de Dependência**:
   Manutenção do padrão Ports & Adapters (Hexagonal Architecture) para permitir a substituição de provedores (ex: SMTP, Meta WPP, Yampi) sem afetar o núcleo da regra de negócio.
3. **Persistência Robusta em PostgreSQL**:
   Garantia de transações seguras, concorrência sem *race conditions* e esquemas limpos de controle de estado.

---

## 3. Próximos Passos (Especificações Futuras)

* [x] Padronizar todos os arquivos `.md` existentes na pasta `project_decisions/`.
* [x] Adicionar metadados de datas e versão em todos os documentos de decisões para rastreabilidade completa.
* [ ] Incluir detalhamento completo da remodelação de regras de negócio nesta especificação assim que definido.
* [ ] Executar a refatoração via ciclos orientados a testes (TDD).



ok vamos la


quermos fazer uma refatoração tanto na parte de carrinhos quanto na parte de pedidos. nessa primeira rodada
O sistema deve rodar a cada 5 minutos e deve ser chamado pela main rotativamente a cada 5 minutos para verificar 48 horas de pedidos e carrinhos (separados por paginas de 100 em 100. exemplo. se nas últimas 48 horas foram feitos 550 pedidos e 355 carrinhos: 550/100 = 5.5 então 6 consultas e 6 seis arquivos. 355/100 = 3.55 então 4 consultas e 4 arquivos). cada tipo deve estar em pastas diferentes

observações:
 1 - deve-se ser assincrono o processo de consulta dos pedidos e de carrinhos na yampi e criar arquivos intermediários contendo (cada um) 100 pedidos/carrinhos cada. Outro workers são responsáveis por consumir esses arquivos dentro dessas mesmas pastas, excluindo-o assim que terminar de processar. (assim teremos um sistema de consumidor pool não travante). ou seja, um indo pelas orders e outro nos carrinhos

 2 - todos esses valores (de prazos e periodos em segundos) devem ser cadastrados como macros a serem ajustadas em um só lugar. assim como muitas outras que vão acabar  aparecendo. assim eu terei o controle em um só lugar dessas variaveis. nem que seja no topo de cada arquivo.
 3 - a ideia é o worker fabricante, que produz os arquivos. paralelo a eles, tem os que consomem esses arquivos (jsons), os quais devem transformar em dicionários, pegar o status e então, a partir deste, toma decisões, como veremos a frente, assim evitando o processamento completo das informações, só processando quando é de fato necessário.

 4 - o caso de status 99 é o seguinte, toda vez que um pedido entrar no sistema (está se verificando um arquivo da pasta orders), faz-se uma busca rápida (na base de dados) pelo nome do cpf do individuo em O(1) usando o dicionario; se der positivo, faz outra busca com o sku do produto mais caro do pedido atual. Se der check, quer dizer que essa compra que o indivíduo está fazendo é uma recompra e conseguimos captar o cliente de volta. essa busca tem que ser feita só no caso de pedido com pagamento efetuado. (a meta é só conferir se essa compra é uma recompra e marcar)


Cenários:
# Carrinhos abandonados,
      - haverá algo muito parecido com o tratamento dos carrinhos abandonados (não viraram pedidos) comparado ao tratamento dos carrinhos que viraram pedidos. Mas (no caso de carrinho abandonado) haverá um link no email sempre para fazer o usuário retornar ao carrinho abandonado para finalizar a compra. 
      Essa analise só existirá caso o campo de pedido id seja vazio (ou seja o carrinho não foi convertido em pedido, mas pode ser ainda). caso tenha pedido, nem olhe o status, pule direto para o próximo cenário.

E os status de carrinhos abandonados são
   null - Começa assim pois ainda não virou pedido
   15  - caso o status carrinho abandonado seja null e tenha passado 4 horas desde o carrinho ser criado e envia o email cupom 4 
   16  - caso o status carrinho abandonado seja 15 e tenha passado 24 horas desde o carrinho ser criado e envia o email cupom 5 
   17  - caso o status carrinho abandonado seja 16 e tenha passado 48 horas desde o carrinho ser criado e envia o email cupom 6
   18 - cliente perdido
   85, 86 ou 87 - caso de conversão de carrinho abandonado em pedido. carrinho abandonado --> pedido. 70 + (o caso anterior) Envia um email agradecendo por não ter desistido - "email recompra" (não será feito agora, deixar como future implementation)

Obs: os emails cupons 4 5 e 6 são essencialmente muito parecidos com o emails cupom 1 2 e 3. A diferença é inserção de um texto de que o carrinhho foi abandonado, e uma pequena modificação no html para que o botão leve para o carrinho abandonado. O botão deverá encaminhar a pessoa de volta para o carrinho abandonado com objetivo de faze-la finalizar o carrinho e transformá-lo em um pedido. e passa a ser administrado pela outra rotina.
 

# pedido
"cliente fez um carrinho e esse se transformou em um pedido"
há alguns cenários para pedido:

primeiro o algoritmo procura pelo id do carrinho em cart_id O(1) na tabela email_status_table, se der positivo (já existia esse carrinho no banco de dados), anexa pedido_id junto a esse carrinho, pois esses fazem referência a mesma coisa e segue para os cenários de pedido. Se der negativo, cria uma nova linha no banco de dados e adiciona o pedido_id e o cart_id. (não esquecendo de adicionar o cpf do cliente e o sku do produto de maior valor para ambos os casos (atualizar a linha caso ela ja exista, tambem)).


   - fato: o cliente tem no máximo 30 minutos para efetuar o pagamento (se não o pedido é perdido e fica como cancelado)
   status e sua marcação:
      null - o campo está nulo originalmente

      1 - caso ele pague dentro dos 30 min (verifica o estado, caso seja a primeira vez que se olha e não o status era null e agora ja tem a tag "pagamento aprovado" ), ou seja, caso o pedido tenha sido efetuado e pago. deve-se enviar o email 1 (pedido criado e pago com sucesso)e marcar no banco de dados o status 1 e avisa em em X tempo será enviado o código de rastreio
      
      2 - caso pedido realizado, mas enquanto analisa-se o pedido e este ainda está em um intervalo de 30 minutos desde "pedido realizado" e o pagamento ainda não foi realizado (estado de pagamento pendente "Aguardando pagamento"). deve-se enviar o email 2. que contem a confirmação mas também um apelo para incentivar o cliente a efetuar o pagamento e o pix/qr code para o cliente finalizar a compra 
     
     caso o status seja 2, verifica novamente o pagamento:
      3 - envio do email 3 (caso o pagamento seja realizado tag "pagamento realizado(conferir)", deve-se enviar o email 3 que é identico ao email 1 (que só estava esperando a confirmação do pagamento))
      4 - caso não tenha sido pago ainda, entraremos na recuperação do cliente com o envio dos emails com cupom.


### tabela unificada (email_status_table)
a tabela deve conter:
pedido_id (pode ser vazio)| cart_id  (nunca vazio e chave) | data do pedido (timestemp) (pode ser vazio)| data do carrinho (timestemp) (nunca vazio)| CPF do cliente (nunca vazio) | sku (do produto de maior valor do pedido) (nunca vazio) | status global (STG) | status carrinho abandonado (STC)| timestemp ultimo email enviado


## Cupons (rebuy_politics):
casos do cupom (sempre com 10% de desconto)
   5  - caso o status(STG) seja 4 e tenha passado 24 horas desde o pedido e envia o email cupom 1 
   6  - caso o status(STG) seja 5 e tenha passado 48 horas desde o pedido e envia o email cupom 2 
   7  - caso o status(STG) seja 6 e tenha passado 72 horas desde o pedido e envia o email cupom 3 
   8  - cliente perdido (não pagou o pedido dentro do prazo de 30 minutos e já recebeu todos os cupons)
   95, 96 ou 97 - caso de recuperação de client. 90 + (o caso anterior) Envia um email agradecendo por não ter desistido - "email recompra" (não será feito agora, deixar como future implementation) 


ou seja, sempre que o sistema for rodar e o status (STG) for 1 (pago com sucesso), 3 (pagamento realizado dentro do prazo), 8 (perdeu o pedido STG), 18 (perdeu o carrinho abandoando STC), 95, 96 ou 97 (recuperação de cliente em em fase de peido - STG) ou 85, 86 ou 87 (recuperação de cliente em em fase de carrinho abandonado - STC), não fazer nada, só pular, caso seja diferente, prossiga nas analises. 

- Acesso ao banco de dados deve ser travante para não corromper dados e linhas (acesso dos workers cart e dos pedidos devem acessar lock ao bd ou pensarmos numa forma melhor)
- Os emails de recompra serão um algoritmo que fica testando a base de dados e checando possíveis recompras crusando cpf, sku e data. mas isso fica apenas como comentário lá no future implementation, uma vez que será inserido no futuro.




