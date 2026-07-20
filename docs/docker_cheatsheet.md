# Docker & Docker Compose Cheatsheet 🐳

Este guia rápido contém os comandos mais comuns do Docker e Docker Compose para auxiliar no desenvolvimento e manutenção do projeto.

---

## 🛠️ Comandos do Docker Compose (Mais Usados)

### Inicialização e Parada
*   **Subir os serviços em segundo plano (Background/Detached):**
    ```bash
    docker compose up -d
    ```
*   **Parar e remover os containers e redes criados:**
    ```bash
    docker compose down
    ```
*   **Parar e remover containers, redes E volumes persistidos (Cuidado: apaga o banco de dados!):**
    ```bash
    docker compose down -v
    ```
*   **Forçar a reconstrução das imagens ao subir:**
    ```bash
    docker compose up -d --build
    ```

### Execução e Inspeção
*   **Executar um comando em um container que já está rodando (recomendado):**
    ```bash
    docker compose exec [servico] [comando]
    # Exemplo: Rodar o worker de carrinhos abandonados
    docker compose exec app python src/main.py abandoned-carts
    ```
*   **Subir um container temporário para executar um comando e removê-lo depois:**
    ```bash
    docker compose run --rm [servico] [comando]
    # Exemplo: Rodar os testes no container
    docker compose run --rm app python -m unittest discover -s tests
    ```
*   **Visualizar logs em tempo real (foco contínuo):**
    ```bash
    docker compose logs -f
    ```
*   **Visualizar logs de um serviço específico:**
    ```bash
    docker compose logs -f [servico]
    # Exemplo: Logs apenas da aplicação
    docker compose logs -f app
    ```
*   **Listar o status dos containers do projeto:**
    ```bash
    docker compose ps
    ```

---

## 🐋 Comandos Gerais do Docker (CLI)

### Containers
*   **Listar containers ativos:**
    ```bash
    docker ps
    ```
*   **Listar todos os containers (ativos e parados):**
    ```bash
    docker ps -a
    ```
*   **Visualizar o consumo de recursos (CPU, Memória, I/O) em tempo real:**
    ```bash
    docker stats
    ```
*   **Remover um container específico:**
    ```bash
    docker rm [container_id_ou_nome]
    ```
*   **Parar um container específico:**
    ```bash
    docker stop [container_id_ou_nome]
    ```
*   **Acessar o terminal interativo de um container rodando:**
    ```bash
    docker exec -it [container_id_ou_nome] /bin/bash
    # ou com sh, caso não possua bash:
    docker exec -it [container_id_ou_nome] /bin/sh
    ```

### Imagens
*   **Listar imagens locais:**
    ```bash
    docker images
    ```
*   **Remover uma imagem local:**
    ```bash
    docker rmi [image_id]
    ```
*   **Forçar remoção de imagem (quando há containers parados associados):**
    ```bash
    docker rmi -f [image_id]
    ```
*   **Resolver conflitos ao apagar imagens (`conflict: unable to delete...`):**
    *   **Se a imagem está associada a um container parado:**
        1. Remova o container: `docker rm [container_id]`
        2. Ou force a remoção da imagem: `docker rmi -f [image_id]`
    *   **Se a imagem está associada a um container ativo/rodando:**
        1. Pare o container: `docker stop [container_id]`
        2. Remova o container: `docker rm [container_id]`
        3. Remova a imagem: `docker rmi [image_id]`

### Limpeza de Disco (Prune)
*   **Limpar tudo que não está sendo usado (containers parados, redes órfãs, cache de build):**
    ```bash
    docker system prune -a
    ```
*   **Limpar volumes não utilizados (Cuidado: pode apagar dados locais persistidos por containers antigos):**
    ```bash
    docker volume prune
    ```

---

## 🚀 Comandos Específicos Deste Projeto

Com os containers iniciados via `docker compose up -d`, você pode usar estes atalhos para interagir com a aplicação:

*   **Verificar logs da aplicação:**
    ```bash
    docker compose logs -f app
    ```
*   **Rodar Worker de Carrinhos Abandonados (Dry-Run):**
    ```bash
    docker compose exec app python src/main.py abandoned-carts
    ```
*   **Rodar Worker de Carrinhos Abandonados (Produção):**
    ```bash
    docker compose exec app python src/main.py abandoned-carts --production
    ```
*   **Rodar Worker de Atualização de Pedidos:**
    ```bash
    docker compose exec app python src/main.py orders
    ```
*   **Rodar os Testes Unitários:**
    ```bash
    docker compose exec app python -m unittest discover -s tests
    ```
*   **Acessar o shell interativo do container da aplicação:**
    ```bash
    docker compose exec app /bin/bash
    ```

---

## 🐞 Depuração (Debugging) Local no VS Code

Para acompanhar a execução do código passo a passo e depurar chamadas de funções filhas de forma visual:

1. Abra a aba **"Run and Debug"** (Executar e Depurar) no VS Code.
2. Selecione um dos perfis criados no menu de seleção:
   *   `Python: Worker Abandoned Carts`
   *   `Python: Worker Orders`
3. Adicione breakpoints no editor (clicando na margem esquerda das linhas dos arquivos `.py`) e aperte **F5**.
   *   *Automação integrada:* O VS Code executará automaticamente a task `Start Database` (`docker compose up -d db`) para subir o banco de dados localmente antes de rodar a depuração, lerá todas as credenciais do seu arquivo `.env` (mapeado via `envFile`) e forçará a utilização do interpretador Python do seu ambiente virtual em `.venv/bin/python3`.

---

### 📁 Logs do Projeto (Nova Pasta)
A aplicação agora grava logs de forma automática no arquivo local `logs/app.log` (mapeado via volume).
*   **Visualizar logs no Host em tempo real:**
    ```bash
    tail -f logs/app.log
    ```
*   **Redirecionar saída para outro arquivo de log se necessário:**
    ```bash
    # Como os logs saem no stdout, você pode redirecionar para um log customizado:
    docker compose exec app python src/main.py abandoned-carts >> log_custom.log
    
    # Se quiser capturar também o stderr (erros do python/flask):
    docker compose exec app python src/main.py abandoned-carts >> log_custom.log 2>&1
    ```
