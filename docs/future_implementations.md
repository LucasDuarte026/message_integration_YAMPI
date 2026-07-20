# Future Implementations

Este documento rastreia débitos técnicos propositais e funcionalidades que foram deixadas para implementações futuras, focando na entrega de valor e no roadmap do produto.

## 1. Orquestração e Gatilhos
- **Webhooks (Yampi):** Atualmente o projeto funciona de forma passiva, utilizando `crontab` para buscar dados através de agendamento (polling). No futuro, devemos expor uma API (`FastAPI` ou `Flask`) para receber Webhooks diretamente da Yampi sempre que um carrinho for abandonado ou atualizado.

## 2. Persistência de Dados e Estado
- **Banco de Dados Descentralizado (Nuvem):** O projeto utiliza `SQLite` local para marcar quais carrinhos já receberam mensagem (evitando envios duplicados). Ao migrar para um ambiente de múltiplos *workers* ou nuvem (ex: AWS Lambda), essa dependência local impedirá escalabilidade. **Migração futura:** Utilizar um banco de dados em nuvem, como PostgreSQL, Redis ou DynamoDB.

## 3. Réguas de Comunicação (Abandoned Cart)
- **Mensagem 2 (Email):** Atualmente programado para disparar apenas a 1ª mensagem (via WhatsApp) após 2 horas. A "Mensagem 2", que deve ocorrer 2 dias após o abandono, deverá utilizar o canal de E-mail.
- **Conteúdo Específico:** Para a v1, estamos apenas extraindo os dados possíveis. A análise comportamental e inserção de cupons dinâmicos/links parametrizados precisam ser definidos e incorporados aos *templates* das mensagens.
- **Exclusão de Pastas Temporárias de Sucesso:** Atualmente, as pastas individuais `emails/cart_<cart_id>/` de cada disparo são criadas e preservadas no workspace para fins de debug e auditoria. Em produção futura, após o envio do e-mail concluir com sucesso sem lançar exceções, a pasta correspondente deve ser removida automaticamente para otimizar o uso de armazenamento físico.

## 4. Mensageria e CPaaS
- **Resiliência e Fallback:** Implementar uma cadeia de *Fallback* no serviço de envio de mensagem. Se a plataforma de WhatsApp recusar a mensagem, ou o número for inválido, o sistema tentará enviar um SMS ou E-mail como alternativa.
- **Definição do Provedor:** Analisar a pesquisa do artefato de CPaaS e integrar a API vencedora utilizando o contrato `MessageProviderProtocol`.
- **Integração Fina do Webhook WhatsApp (WPP Meta Message):** Atualmente, o servidor Flask em `src/webhook_server.py` apenas escuta e loga os eventos no terminal. A funcionalidade futura integrada do webhook de WhatsApp (Meta Message) deve gravar esses eventos (como status `read`, `delivered`, `failed`) diretamente no PostgreSQL (`db`), permitindo rastreabilidade do engajamento do cliente e atualizações de elegibilidade em tempo real.
