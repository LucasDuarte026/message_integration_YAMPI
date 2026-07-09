# Core (Infraestrutura Base)

## Objetivo
O diretório `core` abriga os componentes básicos de infraestrutura interna que suportam a aplicação. São os componentes que lidam com estado interno, configurações e nossa própria fonte de dados primária (API Yampi).

## Arquivos e Responsabilidades
- **`config.py`**: Gerenciador centralizado de variáveis de ambiente e credenciais. Garante a segurança retirando dados sensíveis do restante do código.
- **`client.py`**: O cliente robusto `YampiClient`. Implementa as requisições HTTP, paginação, fallback, rate limits e autenticação para consumir a API da Yampi.
- **`db.py`**: Implementação concreta em SQLite do repositório de persistência (`StateRepositoryProtocol`). Serve para salvar o estado da aplicação (ex: controle de disparo de mensagens duplicadas).

## 🚨 Diretiva de Manutenção (Para IA)
> [!IMPORTANT]
> Se você modificar, adicionar ou remover qualquer arquivo de infraestrutura neste diretório, **DEVE** atualizar este arquivo `README.md` imediatamente para refletir essas mudanças arquiteturais.
