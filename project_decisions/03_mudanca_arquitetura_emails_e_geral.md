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
