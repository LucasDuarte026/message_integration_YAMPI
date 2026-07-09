# Workers (Regras de Negócio / Use Cases)

## Objetivo
É aqui que as regras de negócio da loja orquestram as dependências. Os *workers* são sub-programas projetados para realizar tarefas específicas (ex: Carrinho Abandonado).
Eles **nunca** instanciam clientes HTTP ou Bancos de Dados diretamente; eles recebem tudo via **Injeção de Dependência** em seus construtores e lidam exclusivamente com a lógica.

## Arquivos e Responsabilidades
- **`abandoned_cart.py`**: Implementa a classe `AbandonedCartProcessor`. Consulta os carrinhos via API, filtra pela janela de horas (ex: 2h após abandono), verifica o estado do disparo local para evitar duplicidade e orquestra o provedor de mensagem para contatar o cliente.

## 🚨 Diretiva de Manutenção (Para IA)
> [!IMPORTANT]
> Se você criar uma nova rotina (ex: `payment_reminder.py` para boletos a vencer), **DEVE** atualizar este arquivo `README.md` explicando o fluxo lógico que foi implementado e quais as dependências injetadas que este novo worker utiliza.
