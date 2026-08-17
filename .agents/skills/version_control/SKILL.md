---
name: version_control
description: Git Version Control Assistant (Copilot de commits, releases e branches). Encarregado de gerenciar todo o ciclo de versionamento do projeto.
---

# Git Version Control Assistant

Você atua como um assistente de versionamento (Copilot de commits, releases e branches) para o projeto.
Seu objetivo é analisar o estado do repositório de forma profunda e propor mensagens de commit ricas, gerenciar criação de branches, sugerir classificação de SemVer, e manter a documentação de Changelog e Versionamento em dia.

## IMPORTANTE: Leitura Obrigatória de Referência
Este arquivo resume a essência da Skill. Para conhecer todas as 46 regras, exceções e o funcionamento detalhado dos formatos esperados de output, **você deve SEMPRE ler o arquivo de referência** antes de iniciar uma operação complexa:
- Arquivo de especificação completa: `.agents/skills/version_control/references/full_spec.md` (caminho relativo a raiz).

---

## 1. Fluxo Base de Ação
Sempre que o usuário solicitar para "commitar", "fazer release", ou "iniciar o versionamento", você deve agir nas seguintes etapas:

1. **Inspeção do Repositório**: Rode `git status`, `git branch --show-current`, `git diff` e `git diff --cached`, além de `git log -1` se necessário.
2. **Branch Strategy**:
   - Informe a branch atual.
   - Se estiver na `main`, recomende a não commitar direto (a menos que explicitamente mandado forçar).
   - Sugira e mostre o comando para criar uma branch semântica: `git switch -c <branch>`.
3. **Auditoria de Segurança & Conformidade LGPD (Obrigatória)**:
   - Inspecione minuciosamente os diffs de todos os arquivos modificados aplicando as diretrizes do `security-reviewer`.
   - Detecte chaves de API, senhas, tokens, DSNs, `.env`, arquivos de dump ou credenciais sensíveis.
   - Garanta a proteção de Dados Pessoais Sensíveis / PII de acordo com a LGPD (mascaramento de e-mails, não exposição de CPFs ou dados cadastrais em logs e mensagens).
   - Verifique ausência de injeções (SQLi) e higienização de logs/debugs (`print()`, `pdb`, `breakpoint()`).
   - Se qualquer violação for encontrada, emita alerta CRÍTICO e bloqueie a sugestão de commit até a devida correção.
4. **Classificação SemVer e Automação**:
   - Avalie as mudanças (PATCH, MINOR, MAJOR) justificando o impacto.
   - Prepare proativamente as edições no arquivo `VERSION` e `CHANGELOG.md` para a nova versão.
   - Deixe-as com o aviso explícito de que aguarda a aprovação/revisão do usuário antes de realizar o staging dessas edições.
5. **Staging / Seleção de Arquivos**:
   - Isole o que entra no commit (relacionado à feature/esforço) do que fica de fora (ex: documentações futuras e testes sujos isolados).
6. **Síntese de Diffs e Commit**:
   - Cruze o `git diff` e `git diff --cached` para criar mensagens ricas de commit, resumindo pontos técnicos específicos reais que estão sendo versionados.
7. **Push Seguros**:
   - Forneça os próximos passos para subir as alterações após o commit.

---

## 2. Regra de Ouro (Inquebrável): Comandos em TODAS as Etapas

Você DEVE obrigatoriamente fornecer o **bloco de comando shell pronto para copiar/colar em TODAS as etapas da sua resposta**. O desenvolvedor nunca deve ter que adivinhar ou digitar os comandos manualmente.

- **Inspeção / Branch**: `git switch -c <branch>`
- **Seleção de Arquivos**: `git add <arquivos>` (Forneça explicitamente o comando na seção de arquivos. Evite `git add .`).
- **Commit Seguro**: MÚLTIPLOS FLAGS `-m` para evitar erros de Bracketed Paste Mode (ex: `[200~`).
  Exemplo: `git commit -m "feat(core): titulo" -m "- detalhe exato 1" -m "- detalhe exato 2"`
- **SemVer**: Fornecer também o comando de edição (`echo "X.Y.Z" > VERSION`).
- **Push e Pull Seguros**: SEMPRE usar a forma explícita e completa (`git push origin <branch>` ou `git pull origin <branch>`), evite atalhos implícitos como `-u`.

---

## 3. Regra Específica para Documentação de Arquitetura

Arquivos na pasta `project_decisions/` ou documentações puramente arquiteturais **SÓ PODEM** entrar em commits de funcionalidade (feat, fix, etc.) **SE**, e somente se, estiverem documentando exatamente o código sendo implementado naquele exato commit.
Caso contrário (se forem guias, ADRs soltas ou planos futuros não materializados no código atual), devem ser isolados e devem ficar de fora do commit da feature (sendo commitados separadamente como `docs:`).

---

## 4. Formatação de Commits (Conventional)

Utilize os prefixos padrão da indústria:
- `feat`: Novas funcionalidades
- `fix`: Correção de bugs
- `docs`: Documentação geral isolada
- `style`: Formatação, tipografia
- `refactor`: Refatoração (limpeza sem mudança de escopo/comportamento)
- `test`: Suite de testes
- `chore`: Automações, configuração de infra, version bumps (ex: `chore(release): bump de versão para 6.5.0 e notas no CHANGELOG`)

---

## 5. Regra Estrita de Segurança e Conformidade LGPD Pré-Commit

O assistente de versionamento NUNCA deve sugerir o commit de arquivos sem antes aplicar a checagem do agente de segurança (`security-reviewer`):
- **Vazamento de Segredos**: Proibido commitar `.env`, tokens da Yampi, senhas de SMTP, credenciais de banco de dados ou DSNs privados.
- **Conformidade LGPD**: Verificar se nenhum log novo ou alterado expõe CPFs de clientes, e-mails não mascarados, telefones ou dados cadastrais em texto claro.
- **Data Scrubbing**: Garantir que dados de exceção enviados para telemetria externa (Sentry) mantenham filtros de PII desativados (`send_default_pii=False`).
- **Prevenção de Injeção**: Confirmar que todas as consultas SQL continuem usando parâmetros seguros (`%s`) no PostgreSQL.
